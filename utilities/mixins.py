import pandas as pd
from django.http import HttpResponse
from django.db.models import Model
from rest_framework.response import Response
from utilities import messages
from rest_framework import status
from django.http import StreamingHttpResponse
import csv

class CSVDownloadMixin:
    def download_csv(self, request, queryset, serializer_class, fields=None):
        if not queryset.exists():
            return Response({
                'message': "Empty queryset",
                'status': status.HTTP_204_NO_CONTENT,
                'data': None
            }, status=status.HTTP_204_NO_CONTENT)

        serializer = serializer_class(context={'request': request})
        all_field_names = list(serializer.get_fields().keys())

        if fields:
            invalid_fields = set(fields) - set(all_field_names)
            if invalid_fields:
                return Response({
                    'message': f"Invalid fields: {', '.join(invalid_fields)}",
                    'status': status.HTTP_400_BAD_REQUEST,
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            field_names = fields
        else:
            field_names = all_field_names

        def stream_csv_data():
            # Write the header
            yield ','.join(field_names) + '\n'
            
            # Write the data rows
            for instance in queryset.iterator():
                serializer = serializer_class(instance, context={'request': request})
                row = [str(serializer.data.get(field, '')) for field in field_names]
                yield ','.join(row) + '\n'

        response = StreamingHttpResponse(stream_csv_data(), content_type='text/csv')
        model = queryset.model
        response['Content-Disposition'] = f'attachment; filename="{model._meta.model_name}.csv"'

        return response



# class CSVDownloadMixin:
#     def download_csv(self, request, queryset, serializer_class, fields=None):
#         if not queryset.exists():
#             return Response({
#                 'message': messages.EMPTY_QS,
#                 'status': status.HTTP_204_NO_CONTENT,
#                 'data': None
#             }, status=status.HTTP_204_NO_CONTENT)

#         # Initialize the serializer to get the available fields
#         serializer = serializer_class(context={'request': request})
#         all_field_names = list(serializer.get_fields().keys())

#         # Determine fields to include in the CSV
#         if fields:
#             # Ensure that the requested fields are valid
#             invalid_fields = set(fields) - set(all_field_names)
#             if invalid_fields:
#                 return Response({
#                     'message': f"Invalid fields: {', '.join(invalid_fields)}",
#                     'status': status.HTTP_400_BAD_REQUEST,
#                     'data': None
#                 }, status=status.HTTP_400_BAD_REQUEST)
#             field_names = fields
#         else:
#             field_names = all_field_names

#         # Serialize the queryset with the selected fields
#         serializer = serializer_class(queryset, many=True, context={'request': request})
#         data = [{field: item[field] for field in field_names} for item in serializer.data]

#         # Convert the serialized data to a DataFrame
#         df = pd.DataFrame(data)

#         # Create the HttpResponse object with the appropriate CSV header
#         response = HttpResponse(content_type='text/csv')
#         model = queryset.model
#         response['Content-Disposition'] = f'attachment; filename="{model._meta.model_name}.csv"'

#         # Use Pandas to write the DataFrame to the response
#         df.to_csv(path_or_buf=response, index=False)

#         return response
