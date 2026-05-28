import os
import sys
from pathlib import Path
import django
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esg_core.settings')
django.setup()
from esg_pipeline.models import EmissionRecord

# Convert advisory-only flagged records to APPROVED
advisory_only = EmissionRecord.objects.filter(status=EmissionRecord.Status.PENDING_REVIEW)
count = 0
for r in advisory_only:
    flags = r.data_quality_flags or []
    if not any((f.startswith('DATA_PARSE_ERROR') or f in ('NEGATIVE_USAGE_DETECTED', 'UNMAPPED_AIRPORT_CODE')) for f in flags):
        r.status = EmissionRecord.Status.APPROVED
        r.save()
        count += 1
print('Updated', count, 'records from PENDING_REVIEW to APPROVED (advisory-only flags)')
