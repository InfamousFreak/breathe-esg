import os
import sys
from pathlib import Path
import django
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esg_core.settings')
django.setup()
from esg_pipeline.models import DataIngestionRun, EmissionRecord

run = DataIngestionRun.objects.filter(source_type=DataIngestionRun.SourceType.SAP_PROCUREMENT).order_by('-uploaded_at').first()
print('Run:', run.id, run.uploaded_at.isoformat())
for rec in run.records.filter(status=EmissionRecord.Status.PENDING_REVIEW):
    mblnr = rec.raw_payload.get('MBLNR') if isinstance(rec.raw_payload, dict) else None
    print(rec.id, 'MBLNR=', mblnr, 'flags=', rec.data_quality_flags, 'raw_qty=', rec.raw_payload.get('MENGE'))
