import logging
import json
import facebook
import moneyed
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import parsers
from rest_framework import mixins, status, exceptions
from django.views.decorators.csrf import csrf_exempt


from BdayApp.serializers import EventSerializer, Event, Wallet
from BdayApp.UserProfileView import UserProfileView
from BdayApp.models import UnreadChatBuffer

logger = logging.getLogger(__name__)


class EventView(generics.CreateAPIView,generics.RetrieveUpdateAPIView):

    model = Event
    parser_classes = (parsers.JSONParser,parsers.MultiPartParser,parsers.FormParser,)
    serializer_class = EventSerializer

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    @staticmethod
    def get_event(access_token, id, user_in=None):
        try:
            logger.info("Starting function get_event")
            logger.info("access token is "+access_token+" event id is "+id)
            user = UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")
            event = Event.objects.select_related('event_wallet').get(pk=id)
            logger.info("event object found with id "+id)
            if user_in is None:
                if user in event.admin.all() or user in event.members.all():
                    logger.info("Completing function get_event")
                    return event
                else:
                    raise exceptions.PermissionDenied()
            elif user_in is "admin":
                if user in event.admin.all():
                    logger.info("Completing function get_event")
                    return event
                else:
                    raise exceptions.PermissionDenied()
            elif user_in is "member":
                if user in event.members.all():
                    logger.info("Completing function get_event")
                    return event
                else:
                    raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventView.handle_error(e)

    def get(self, request, *args, **kwargs):
        try:
            logger.info("Starting GET method")
            access_token = kwargs['access_token']
            id = kwargs['id']
            logger.info("access token is "+access_token+" event id is "+id)
            event = EventView.get_event(access_token, id)
            serializer = EventSerializer(event)
            logger.info("Completing GET method")
            return response.Response(serializer.data)
        except Exception as e:
            EventView.handle_error(e)

    def put(self, request, *args, **kwargs):
        try:
            logger.info("Starting PUT method")
            access_token = kwargs['access_token']
            id = kwargs['id']
            logger.info("access token is " + access_token + " event id is " + id)
            event = EventView.get_event(access_token, id, user_in="admin")
            serializer = EventSerializer(event, data=request.data, partial=True)
            if request.FILES:
                event.picture = request.FILES['file_field']
                logger.info("found file in request")
            else:
                event.picture = None
            if serializer.is_valid():
                serializer.save()
                event.save()
                logger.info("Completing PUT method")
                return response.Response(serializer.data)
        except Exception as e:
            EventView.handle_error(e)

    @staticmethod
    def create_wallet(event):
        logger.info("Starting function create_wallet")
        minimum_balance = moneyed.Money(0,'INR')
        maximum_balance = moneyed.Money(0,'INR')
        associated_event = event
        type = 'E'
        logger.info("Completing function create_wallet")
        return Wallet.objects.create(minimum_balance, maximum_balance, type, 'INR',None, associated_event)

    def post(self, request, *args, **kwargs):
        try:
            logger.info("Starting POST method")
            access_token = kwargs['access_token']
            logger.info("access token is "+access_token)
            user = UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")
            file = None
            if request.FILES:
                file = request.FILES['file_field']
                logger.info("file found in request")
            else:
                file = None
            end_date = None
            type = 'DEFAULT'
            if 'end_date' in request.data:
                end_date = request.data['end_date']
                logger.info("end date is "+end_date)
            if 'type' in request.data:
                type = request.data['type']
                logger.info("type is "+type)
            event = Event.objects.create_event(admin=user,name=request.data['name'],start_date=request.data['start_date'],end_date=end_date,picture=file,type=type)
            logger.info("event created with name "+request.data['name']+" start date "+request.data['start_date']+" type "+type)
            minimum_balance = moneyed.Money(0, 'INR')
            maximum_balance = moneyed.Money(100000, 'INR')
            wallet = Wallet.objects.create_wallet(minimum_balance, maximum_balance, 'E', 'INR', None, event)
            wallet.save()
            logger.info("wallet created")
            # chat_buffer = UnreadChatBuffer.objects.create(event=event, user=user, last_read_chat=None)
            # chat_buffer.save()
            serializer = EventSerializer(event)
            logger.info("Completing POST method")
            return response.Response(serializer.data)
        except Exception as e:
            EventView.handle_error(e)
