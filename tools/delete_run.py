import os
import sys
from pathlib import Path
import django
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esg_core.settings')

import django
django.setup()
from esg_pipeline.models import DataIngestionRun

RUN_ID = '284583fb-b9ae-4a47-b1ec-5b00ead69e77'
try:
    run = DataIngestionRun.objects.get(id=RUN_ID)
    print('Deleting run', run.id, run.source_type, run.uploaded_at, 'and', run.records.count(), 'records')
    run.delete()
    print('Deleted')
except DataIngestionRun.DoesNotExist:
    print('Run not found')
