from BdayApp.serializers import ReminderSerializer
from BdayApp.models import UserProfile, BdayAppUser, Reminder
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions
from rest_framework.parsers import FormParser, FileUploadParser, MultiPartParser
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ReminderView(generics.GenericAPIView):

    model = Reminder
    serializer_class = ReminderSerializer
    parser_classes = (FormParser, MultiPartParser)

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    @staticmethod
    def get_reminder(access_token,id):
        try:
            user = UserProfileView.get_profile(access_token).user
            logger.info(id)
            reminder = Reminder.objects.get(pk=id)
            logger.info(reminder.name)
            if user == reminder.user:
                return reminder
            else:
                raise exceptions.PermissionDenied()
        except Reminder.DoesNotExist:
            raise exceptions.NotFound("Reminder does not exist")
        except Exception as e:
            ReminderView.handle_error(e)

    def get(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            reminder = ReminderView.get_reminder(access_token,id)
            logger.info(reminder.name)
            serializer = ReminderSerializer(reminder)
            return response.Response(serializer.data)
        except Exception as e:
            ReminderView.handle_error(e)

    def put(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            reminder = ReminderView.get_reminder(access_token, id)
            logger.info(reminder.name)
            if request.FILES:
                reminder.picture = request.FILES['file_field']
            else:
                reminder.picture = None

            serializer = ReminderSerializer(reminder, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return response.Response(serializer.data)
        except Exception as e:
            ReminderView.handle_error(e)

    def post(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        try:
            if request.FILES:
                file = request.FILES['file_field']
            else:
                file = None
            user = UserProfileView.get_profile(access_token).user
            reminder = Reminder.objects.create_reminder(request.data['name'],
                                                        request.data['date'],
                                                        user,
                                                        picture=file, type='CUSTOM')
            reminder.save()
            serializer = ReminderSerializer(reminder)
            return response.Response(serializer.data)
        except Exception as e:
            ReminderView.handle_error(e)

    def delete(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            user = UserProfileView.get_profile(access_token).user
            reminder = Reminder.objects.get(pk=id)
            if user == reminder.user:
                reminder.delete()
                return response.Response(status=status.HTTP_202_ACCEPTED)
            else:
                raise exceptions.PermissionDenied()
        except Reminder.DoesNotExist:
            raise  exceptions.NotFound("Reminder does not exist")
        except Exception as e:
            ReminderView.handle_error(e)



