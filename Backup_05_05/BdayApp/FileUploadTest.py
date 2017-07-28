from BdayApp.models import FileTestMode
from BdayApp import serializers
from rest_framework import generics
from rest_framework import response
from rest_framework import parsers
import logging
import moneyed
import json
import facebook

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FileUploadTest(generics.GenericAPIView):
    model = FileTestMode
    parser_classes = (parsers.MultiPartParser,parsers.FormParser,)
    serializer_class = serializers.FileTest


    def post(self, request, format=None):
        try:
            if request.FILES:
                files = request.FILES
                print files['file_field']
                file_model = FileTestMode.objects.create()
                file_model.file_field = files['file_field']
                file_model.save()
                serializer = serializers.FileTest(file_model)
                return response.Response(serializer.data)
            else:
                return response.Response(request.data)
        except Exception as e:
            print e.message

