from rest_framework import serializers
from .models import EmissionRecord, DataIngestionRun

class FileUploadSerializer(serializers.Serializer):
    """Simple serializer to handle the multipart/form-data file upload."""
    file = serializers.FileField()

class EmissionRecordSerializer(serializers.ModelSerializer):
    """
    Exposes exactly what the React analyst dashboard needs to render the review grid.
    """
    class Meta:
        model = EmissionRecord
        fields = [
            'id', 
            'status', 
            'data_quality_flags', 
            'raw_payload', 
            'activity_date_start',
            'normalized_quantity', 
            'normalized_unit'
        ]