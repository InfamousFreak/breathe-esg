from django.urls import path
from .views import SAPIngestionView, AnalystDashboardView, UtilityIngestionView, TravelWebhookView

urlpatterns = [
    # Dashboards
    path('api/v1/dashboard/pending-review/', AnalystDashboardView.as_view(), name='api_pending_review'),
    
    # Ingestion Endpoints
    path('api/v1/ingest/sap/', SAPIngestionView.as_view(), name='api_ingest_sap'),
    path('api/v1/ingest/utility/', UtilityIngestionView.as_view(), name='api_ingest_utility'),
    path('api/v1/ingest/travel/', TravelWebhookView.as_view(), name='api_ingest_travel'),
]