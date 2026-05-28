import os
import sys
from pathlib import Path
import django

# Ensure project root is on sys.path so Django settings can be imported
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esg_core.settings')
django.setup()
from esg_pipeline.models import EmissionRecord
qs = EmissionRecord.objects.filter(status=EmissionRecord.Status.PENDING_REVIEW)
print('pending_count=', qs.count())
for r in qs.order_by('-created_at')[:24]:
    print(r.id, r.created_at.isoformat(), r.ingestion_run.source_type, r.data_quality_flags)
