import csv
import json
import math
from datetime import datetime

from django.db import transaction

from .models import EmissionRecord, DataIngestionRun, Organization


class SAPIngestionService:
    """Simple SAP CSV ingestion service used by the API views.

    This is a lightweight implementation that mirrors the utility ingestion
    flow but expects SAP-specific field names. It is intentionally forgiving
    (flags parse errors instead of raising) so the analyst dashboard can pick
    up problematic rows for human review.
    """

    @classmethod
    @transaction.atomic
    def process_csv(cls, file_obj, organization, user):
        run = DataIngestionRun.objects.create(
            organization=organization,
            source_type=DataIngestionRun.SourceType.SAP_PROCUREMENT,
            uploaded_by=user,
        )

        decoded_file = file_obj.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        records_to_create = []

        for row in reader:
            flags = []
            status = EmissionRecord.Status.APPROVED

            try:
                # SAP CSVs include BUDAT (posting date) and CPUDT (entry date).
                # Try common SAP date columns first, then fall back to generic names.
                period = (
                    row.get('BUDAT') or row.get('CPUDT') or row.get('Period') or row.get('Period_Start') or ''
                )
                period_str = str(period).strip()
                activity_date = None
                if period_str:
                    parsed = None
                    # Accept multiple formats including DD.MM.YYYY commonly used in SAP exports
                    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%Y%m%d', '%d-%m-%Y', '%m/%d/%Y'):
                        try:
                            parsed = datetime.strptime(period_str, fmt).date()
                            break
                        except Exception:
                            continue
                    if parsed:
                        activity_date = parsed
                    else:
                        flags.append(f"DATA_PARSE_ERROR: invalid period '{period_str}'")

                # SAP uses 'MENGE' for quantity and 'MEINS' for unit
                usage_raw = row.get('MENGE') or row.get('Quantity') or row.get('Menge') or row.get('Usage') or ''
                unit_raw = row.get('MEINS') or row.get('MEINS'.lower()) or row.get('MEINS'.upper()) or ''
                try:
                    usage_clean = str(usage_raw).replace(',', '').strip()
                    usage_val = float(usage_clean) if usage_clean != '' else 0.0
                    if usage_val < 0:
                        flags.append('NEGATIVE_USAGE_DETECTED')
                except Exception:
                    flags.append(f"DATA_PARSE_ERROR: Usage not numeric ('{usage_raw}')")
                    usage_val = 0.0

                # For fuels we do not yet apply per-fuel emission factors in this
                # prototype; record the normalized quantity as the raw value and
                # leave CO2 calculation to a later step. Use a simple placeholder
                # factor for now (0.001 tons per unit) so fields are populated.
                co2_tons = (usage_val * 0.001)

            except Exception as e:
                flags.append(f"DATA_PARSE_ERROR: {str(e)}")
                activity_date, kwh_usage, co2_tons = None, 0.0, 0.0

            # Only treat certain flags as blocking. Some flags (e.g. billing
            # cycles that cross month boundaries) are advisory and should not
            # automatically force analyst review.
            blocking = False
            for f in flags:
                if f.startswith('DATA_PARSE_ERROR') or f in ('NEGATIVE_USAGE_DETECTED', 'UNMAPPED_AIRPORT_CODE'):
                    blocking = True
                    break
            if blocking:
                status = EmissionRecord.Status.PENDING_REVIEW

            records_to_create.append(
                EmissionRecord(
                    organization=organization,
                    ingestion_run=run,
                    raw_payload=row,
                    activity_date_start=activity_date,
                    activity_date_end=activity_date,
                    normalized_quantity=usage_val,
                    normalized_unit=(unit_raw or ''),
                    co2_equivalent_tons=co2_tons,
                    scope_category=EmissionRecord.Scope.SCOPE_2,
                    status=status,
                    data_quality_flags=flags,
                )
            )

        EmissionRecord.objects.bulk_create(records_to_create)
        return run

class UtilityIngestionService:
    @classmethod
    @transaction.atomic
    def process_csv(cls, file_obj, organization, user):
        run = DataIngestionRun.objects.create(
            organization=organization,
            source_type=DataIngestionRun.SourceType.UTILITY_CSV,
            uploaded_by=user
        )
        decoded_file = file_obj.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        records_to_create = []

        for row in reader:
            flags = []
            status = EmissionRecord.Status.APPROVED
            # Helper: try multiple header names and date formats
            def parse_date_field(val):
                if not val:
                    return None
                s = val.strip()
                if s == '':
                    return None
                for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y%m%d', '%m/%d/%Y'):
                    try:
                        return datetime.strptime(s, fmt).date()
                    except Exception:
                        continue
                return None

            # Accept both 'Billing_Period_Start' and 'Period_Start' etc.
            start_raw = row.get('Billing_Period_Start') or row.get('Period_Start') or row.get('BillingStart') or ''
            end_raw = row.get('Billing_Period_End') or row.get('Period_End') or row.get('BillingEnd') or ''

            start_date = parse_date_field(start_raw)
            end_date = parse_date_field(end_raw)

            if start_date and end_date and start_date.month != end_date.month:
                flags.append('NON_CALENDAR_ALIGNED')

            # Usage value + unit. Support 'Usage_Value' and 'Usage_kWh'. Convert MWh to kWh.
            usage_raw = row.get('Usage_Value') or row.get('Usage_kWh') or row.get('Usage') or ''
            unit_raw = row.get('Unit_Of_Measure') or row.get('Unit_Of_Measure'.lower()) or row.get('Unit') or ''
            unit = unit_raw.strip().lower() if isinstance(unit_raw, str) else ''

            try:
                # Allow numbers with commas
                usage_clean = str(usage_raw).replace(',', '').strip()
                usage_val = float(usage_clean)
                # Convert MWh -> kWh
                if unit == 'mwh':
                    kwh_usage = usage_val * 1000.0
                else:
                    kwh_usage = usage_val

                if kwh_usage < 0:
                    flags.append('NEGATIVE_USAGE_DETECTED')

                co2_tons = (kwh_usage * 0.4) / 1000
            except Exception as e:
                flags.append(f"DATA_PARSE_ERROR: {str(e)}")
                start_date, end_date, kwh_usage, co2_tons = None, None, 0.0, 0.0

            # As above: only flag as PENDING_REVIEW for blocking conditions.
            blocking = False
            for f in flags:
                if f.startswith('DATA_PARSE_ERROR') or f in ('NEGATIVE_USAGE_DETECTED', 'UNMAPPED_AIRPORT_CODE'):
                    blocking = True
                    break
            if blocking:
                status = EmissionRecord.Status.PENDING_REVIEW

            records_to_create.append(
                EmissionRecord(
                    organization=organization,
                    ingestion_run=run,
                    raw_payload=row,
                    activity_date_start=start_date,
                    activity_date_end=end_date,
                    normalized_quantity=kwh_usage,
                    normalized_unit='kWh',
                    co2_equivalent_tons=co2_tons,
                    scope_category=EmissionRecord.Scope.SCOPE_2, # Electricity is Scope 2
                    status=status,
                    data_quality_flags=flags
                )
            )

        EmissionRecord.objects.bulk_create(records_to_create)
        return run
    
class TravelIngestionService:
    # Mock Airport Coordinate DB (Latitude, Longitude)
    AIRPORT_DB = {
        "JFK": (40.6413, -73.7781),
        "LHR": (51.4700, -0.4543),
        "DEL": (28.5562, 77.1000),
        "SFO": (37.6213, -122.3790)
    }

    @staticmethod
    def haversine_distance(coord1, coord2):
        # Calculates distance in km between two lat/long points
        R = 6371.0 # Earth radius in km
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    @classmethod
    @transaction.atomic
    def process_json_webhook(cls, payload_list, organization, user):
        run = DataIngestionRun.objects.create(
            organization=organization,
            source_type=DataIngestionRun.SourceType.CONCUR_TRAVEL,
            uploaded_by=user
        )

        records_to_create = []

        for trip in payload_list:
            flags = []
            status = EmissionRecord.Status.APPROVED
            
            origin = trip.get('origin_airport')
            dest = trip.get('destination_airport')
            distance_km = 0
            co2_tons = 0

            if origin in cls.AIRPORT_DB and dest in cls.AIRPORT_DB:
                distance_km = cls.haversine_distance(cls.AIRPORT_DB[origin], cls.AIRPORT_DB[dest])
                # Mock math: 0.15 kg CO2e per passenger km
                co2_tons = (distance_km * 0.15) / 1000
            else:
                flags.append("UNMAPPED_AIRPORT_CODE")

            if flags:
                status = EmissionRecord.Status.PENDING_REVIEW

            records_to_create.append(
                EmissionRecord(
                    organization=organization,
                    ingestion_run=run,
                    raw_payload=trip,
                    normalized_quantity=distance_km,
                    normalized_unit='km',
                    co2_equivalent_tons=co2_tons,
                    scope_category=EmissionRecord.Scope.SCOPE_3, # Business travel is Scope 3
                    status=status,
                    data_quality_flags=flags
                )
            )

        EmissionRecord.objects.bulk_create(records_to_create)
        return run