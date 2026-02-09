from django.db import models
from django.utils.timezone import now

class MetaData(models.Model):   
    endpoint = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    keywords = models.TextField(blank=True, null=True) 
    canonicalURL = models.URLField(blank=True, null=True)
    
    createdBy = models.CharField(max_length=25, default='system')
    createdWhen = models.DateTimeField(auto_now_add=True)
    touchedBy = models.CharField(max_length=25, default='system')
    touchedWhen = models.DateTimeField(auto_now=True)  

def __str__(self):
    return f"{self.title} ({self.endpoint})"
