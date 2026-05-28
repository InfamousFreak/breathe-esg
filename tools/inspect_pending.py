from esg_pipeline.models import EmissionRecord

qs = EmissionRecord.objects.filter(status=EmissionRecord.Status.PENDING_REVIEW)
print('pending_count=', qs.count())
for r in qs.order_by('-created_at')[:12]:
    print(r.id, r.created_at, r.ingestion_run.source_type, r.data_quality_flags)
