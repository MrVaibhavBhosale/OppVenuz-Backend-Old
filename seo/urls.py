from django.urls import path
from .views import GetMetadataListView
urlpatterns = [
     path('getMetadata/', GetMetadataListView.as_view(), name='get_seo_metadata'),    
    #  path('getMetadata/(?P<endpoint>.+)', GetMetadataListView.as_view(), name='get_seo_metadata'),    
]

