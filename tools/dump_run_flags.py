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

run = DataIngestionRun.objects.filter(source_type=DataIngestionRun.SourceType.UTILITY_CSV).order_by('-uploaded_at').first()
print('Run:', run.id, run.uploaded_at.isoformat())
qs = run.records.filter(status=EmissionRecord.Status.PENDING_REVIEW)
print('pending_count=', qs.count())
for rec in qs.order_by('created_at'):
    print('---')
    print('id:', rec.id)
    print('flags:', rec.data_quality_flags)
    print('raw_payload:', rec.raw_payload)
