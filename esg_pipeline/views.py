from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.contrib.auth import get_user_model
User = get_user_model()

from .services import SAPIngestionService
from .models import Organization, EmissionRecord
from .serializers import FileUploadSerializer, EmissionRecordSerializer
from .services import UtilityIngestionService, TravelIngestionService

class SAPIngestionView(APIView):
    """
    POST: Accepts a CSV file, runs it through the validation engine, and saves to DB.
    """
    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            file_obj = serializer.validated_data['file']
            
            # TRADEOFF NOTE FOR YOUR DECISIONS.MD: 
            # In a production app, the Organization would be derived from the user's 
            # JWT token or session. For this 4-day prototype, we grab the first active org.
            organization = Organization.objects.first()
            
            if not organization:
                return Response({"error": "No tenant organization found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                uploading_user = request.user if request.user.is_authenticated else User.objects.first()
                run = SAPIngestionService.process_csv(file_obj, organization, uploading_user)
                return Response({
                    "message": "SAP data ingested successfully.",
                    "run_id": str(run.id)
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                # Catch unexpected catastrophic errors (like wrong file encoding)
                return Response({"error": f"Ingestion failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnalystDashboardView(APIView):
    """
    GET: Fetches all records that have been flagged and require human review.
    """
    def get(self, request):
        # We only want to surface rows that failed validation to the analyst
        flagged_records = EmissionRecord.objects.filter(
            status=EmissionRecord.Status.PENDING_REVIEW
        ).order_by('-created_at')
        
        serializer = EmissionRecordSerializer(flagged_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
class UtilityIngestionView(APIView):
    """POST: Ingests Utility Portal CSVs"""
    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            org = Organization.objects.first()
            user = request.user if request.user.is_authenticated else User.objects.first()
            try:
                run = UtilityIngestionService.process_csv(serializer.validated_data['file'], org, user)
                return Response({"message": "Utility data ingested.", "run_id": str(run.id)}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class TravelWebhookView(APIView):
    """POST: Accepts JSON arrays from mock travel APIs (like Concur)"""
    def post(self, request, *args, **kwargs):
        payload = request.data # Expecting a JSON list: [{"origin_airport": "JFK", ...}]
        org = Organization.objects.first()
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        if not isinstance(payload, list):
            return Response({"error": "Payload must be a JSON array of trips."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            run = TravelIngestionService.process_json_webhook(payload, org, user)
            return Response({"message": "Travel data ingested.", "run_id": str(run.id)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)