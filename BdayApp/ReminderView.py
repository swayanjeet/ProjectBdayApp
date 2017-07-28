import logging
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions
from rest_framework import parsers

from BdayApp.models import Reminder,UserProfile
from BdayApp.serializers import ReminderSerializer
from BdayApp.UserProfileView import UserProfileView

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ReminderView(generics.GenericAPIView):

    model = Reminder
    parser_classes = (parsers.JSONParser,parsers.MultiPartParser,parsers.FormParser,)
    serializer_class = ReminderSerializer

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    @staticmethod
    def get_reminder(access_token, id):
        try:
            logger.info("Starting function get_reminder")
            logger.info("access token is "+access_token+" reminder id is "+id)
            #user = UserProfileView.get_profile(access_token).user
            user = UserProfile.objects.get(profile_id__exact='1069321953161548').user
            logger.info("user found from access token")
            reminder = Reminder.objects.get(pk=id)
            logger.info("reminder found from id")
            if user == reminder.user:
                logger.info("user permitted to access reminder")
                logger.info("Ending function get_reminder")
                return reminder
            else:
                logger.info("user not permitted to access reminder")
                raise exceptions.PermissionDenied()
        except Reminder.DoesNotExist:
            raise exceptions.NotFound("Reminder does not exist")
        except Exception as e:
            ReminderView.handle_error(e)

    def get(self, request, *args, **kwargs):
        try:
            logger.info("Starting function for GET method in ReminderView")
            access_token = kwargs['access_token']
            id = kwargs['id']
            logger.info("access token is "+access_token+" reminder id is "+id)
            reminder = ReminderView.get_reminder(access_token, id)
            logger.info("reminder found from access token and id")
            serializer = ReminderSerializer(reminder)
            logger.info("Completing function for GET method in ReminderView")
            return response.Response(serializer.data)
        except Exception as e:
            ReminderView.handle_error(e)

    def put(self, request, *args, **kwargs):
        try:
            logger.info("Starting function for PUT method in ReminderView")
            access_token = kwargs['access_token']
            id = kwargs['id']
            logger.info("access token is " + access_token + " reminder id is " + id)
            reminder = ReminderView.get_reminder(access_token, id)
            logger.info("reminder found from access token and id")
            if request.FILES:
                reminder.picture_file = request.FILES['file_field']
                logger.info("file field found in PUT request")
            else:
                reminder.picture_file = None
            reminder.save()
            serializer = ReminderSerializer(reminder, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            logger.info("Completing function for GET method in ReminderView")
            return response.Response(serializer.data)
        except Exception as e:
            ReminderView.handle_error(e)


    def post(self, request, *args, **kwargs):
        try:
            logger.info("Starting function for POST method in ReminderView")
            access_token = kwargs['access_token']
            name = request.data['name']
            start_date = request.data['date']
            type = request.data['type']
            if request.FILES:
                file = request.FILES['file_field']
            else:
                file = None
            logger.info("access token is "+access_token)
            logger.info("file object found")
            user = UserProfileView.get_profile(access_token).user
            logger.info("user object found from access token")
            reminder = Reminder.objects.create_reminder(name,
                                                        start_date,
                                                        user,
                                                        picture=None,type=type,picture_file=file)
            logger.info("reminder object created with name "+name+" date "+start_date+" user "+str(user)+" type "+str(type)+" picture_file "+str(file))
            reminder.save()
            logger.info("reminder saved")
            serializer = ReminderSerializer(reminder)
            logger.info("Serializer created")
            logger.info("Ending function for POST method in ReminderView")
            return response.Response(serializer.data)
        except Exception as e:
            ReminderView.handle_error(e)


    def delete(self, request, *args, **kwargs):
        try:
            logger.info("Starting function for DELETE method in ReminderView")
            access_token = kwargs['access_token']
            id = kwargs['id']
            logger.info("access token is "+access_token+" reminder id is "+id)
            user = UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")
            reminder = Reminder.objects.get(pk=id)
            logger.info("reminder found from id")
            if user == reminder.user:
                logger.info("user permitted to delete reminder")
                reminder.delete()
                logger.info("reminder deleted")
                logger.info("Ending function for DELETE method in ReminderView")
                return response.Response(status=status.HTTP_202_ACCEPTED)
            else:
                logger.info("user not permitted to access reminder")
                raise exceptions.PermissionDenied()
        except Reminder.DoesNotExist:
            raise exceptions.NotFound("Reminder does not exist")
        except Exception as e:
            ReminderView.handle_error(e)



