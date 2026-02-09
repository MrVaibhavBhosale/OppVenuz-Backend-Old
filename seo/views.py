from django.http import JsonResponse
from .models import MetaData
from .serializers import MetaDataSerializer
from django.views import View
from django.db import DatabaseError

class GetMetadataListView(View):
    def get(self, request):
        endpoint = request.GET.get("endpoint", "").strip()
        if not endpoint:
            return JsonResponse({"error": "Endpoint is missing."}, status=400)
        try:            
            try:
                seo_metadata = MetaData.objects.get(endpoint=endpoint)
            except MetaData.DoesNotExist:
                # Fallback to 'homepage' metadata if requested endpoint not found
                try:
                    seo_metadata = MetaData.objects.get(endpoint="homepage")
                except MetaData.DoesNotExist:
                    return JsonResponse({"error": "SEO metadata not found, and no default metadata available."}, status=404)

            serializer = MetaDataSerializer(seo_metadata)
            return JsonResponse(serializer.data)

        except DatabaseError:
            return JsonResponse({"error": "Database error occurred"}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)   