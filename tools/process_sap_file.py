import os
import sys
from pathlib import Path
import django
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esg_core.settings')
django.setup()
from esg_pipeline.services import SAPIngestionService
from esg_pipeline.models import Organization

org = Organization.objects.first()
file_path = 'sap_fuel_export_raw.csv'
with open(file_path, 'rb') as f:
    run = SAPIngestionService.process_csv(f, org, None)
print('Created run', run.id)
