from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Organization(models.Model):
    """
    Handles Multi-Tenancy. Every record in the system MUST map back to an Organization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class DataIngestionRun(models.Model):
    """
    Groups records together. If an analyst uploads a CSV with 500 rows, 
    they all belong to one run. Makes bulk deletion or tracking easier.
    """
    class SourceType(models.TextChoices):
        SAP_PROCUREMENT = 'SAP_PROCUREMENT', 'SAP Procurement'
        UTILITY_CSV = 'UTILITY_CSV', 'Utility Portal Export'
        CONCUR_TRAVEL = 'CONCUR_TRAVEL', 'Corporate Travel API'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='ingestion_runs')
    source_type = models.CharField(max_length=50, choices=SourceType.choices)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_type} - {self.uploaded_at.strftime('%Y-%m-%d')}"

class EmissionRecord(models.Model):
    """
    The core State Machine. Tracks a single row of data from RAW -> NORMALIZED -> APPROVED.
    """
    class Status(models.TextChoices):
        STAGING = 'STAGING', 'Raw / Processing'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Analyst Review'
        APPROVED = 'APPROVED', 'Approved & Locked'
        REJECTED = 'REJECTED', 'Rejected'

    class Scope(models.TextChoices):
        SCOPE_1 = 'SCOPE_1', 'Scope 1 (Direct)'
        SCOPE_2 = 'SCOPE_2', 'Scope 2 (Indirect - Energy)'
        SCOPE_3 = 'SCOPE_3', 'Scope 3 (Value Chain)'
        UNASSIGNED = 'UNASSIGNED', 'Pending Categorization'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='emission_records')
    ingestion_run = models.ForeignKey(DataIngestionRun, on_delete=models.CASCADE, related_name='records')
    
    # --- SOURCE OF TRUTH (Immutable) ---
    raw_payload = models.JSONField(
        help_text="The exact, unmodified JSON/dict from the source (SAP, Utility, Travel)."
    )
    
    # --- NORMALIZED DATA (Editable during PENDING_REVIEW) ---
    activity_date_start = models.DateField(null=True, blank=True)
    activity_date_end = models.DateField(null=True, blank=True)
    
    normalized_quantity = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    normalized_unit = models.CharField(max_length=50, blank=True) # e.g., 'kWh', 'metric_tons'
    
    # The computed carbon output
    co2_equivalent_tons = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    
    scope_category = models.CharField(max_length=20, choices=Scope.choices, default=Scope.UNASSIGNED)
    
    # --- PIPELINE METADATA ---
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STAGING)
    data_quality_flags = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of strings flagging issues, e.g., ['UNRECOGNIZED_UNIT', 'SUSPICIOUS_HIGH_VALUE']"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organization.name} - {self.get_scope_category_display()} ({self.status})"

class AuditLog(models.Model):
    """
    Immutable ledger of every change made to an EmissionRecord.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='audit_logs')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    action = models.CharField(max_length=50) # e.g., 'STATUS_CHANGED', 'VALUE_UPDATED', 'APPROVED'
    previous_state = models.JSONField(null=True, blank=True)
    new_state = models.JSONField()
    justification = models.TextField(blank=True, help_text="Why the analyst made this change.")

    def __str__(self):
        return f"{self.action} on {self.record.id} at {self.changed_at}"