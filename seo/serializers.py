from rest_framework import serializers
from .models import MetaData

class MetaDataSerializer(serializers.ModelSerializer):
    canonicalURL = serializers.CharField(allow_null=True, default="")
    keywords = serializers.CharField(allow_null=True, default="")
    class Meta:
        model = MetaData
        fields = ['title', 'description', 'keywords', 'canonicalURL']
        # extra_kwargs = {
        #     'title': {'required': True, 'allow_blank': False},  
        #     'description': {'required': True, 'allow_blank': False},  
        #     'keywords': {'required': False, 'allow_blank': True},  
        #     'canonicalURL': {'required': False, 'allow_blank': True},  
        # }
