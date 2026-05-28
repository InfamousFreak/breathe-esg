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

runs = DataIngestionRun.objects.order_by('-uploaded_at')[:10]
for r in runs:
    count = r.records.count()
    pending = r.records.filter(status=EmissionRecord.Status.PENDING_REVIEW).count()
    sample_flags = list(r.records.values_list('data_quality_flags', flat=True)[:3])
    print(r.id, r.source_type, r.uploaded_at.isoformat(), 'count=', count, 'pending=', pending, 'sample_flags=', sample_flags)
