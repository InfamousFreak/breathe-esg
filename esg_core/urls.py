from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This tells Django: "Hey, look inside esg_pipeline for any other URLs"
    path('', include('esg_pipeline.urls')), 
]