from BdayApp.serializers import EventSerializer, Event, Wallet
from BdayApp.models import UserProfile
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions
import logging
import moneyed
import json
import facebook

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class EventView(generics.GenericAPIView):

    model = Event
    serializer_class = EventSerializer

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    @staticmethod
    def get_event(access_token, id, user_in=None):
        try:
            user = UserProfileView.get_profile(access_token).user
            event = Event.objects.select_related('event_wallet').get(pk=id)
            if user_in is None:
                if user in event.admin.all() or user in event.members.all():
                    return event
                else:
                    raise exceptions.PermissionDenied()
            elif user_in is "admin":
                if user in event.admin.all():
                    return event
                else:
                    raise exceptions.PermissionDenied()
            elif user_in is "member":
                if user in event.members.all():
                    return event
                else:
                    raise exceptions.PermissionDenied()
            logger.info("Completing get event method")
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventView.handle_error(e)


    def get(self, request, access_token, id, *args, **kwargs):
        try:
            event = EventView.get_event(access_token,id)
            serializer = EventSerializer(event)
            return response.Response(serializer.data)
        except Exception as e:
            EventView.handle_error(e)

    def put(self, request, access_token, id, *args, **kwargs):
        try:
            event = EventView.get_event(access_token,id,user_in="admin")
            serializer = EventSerializer(event, data=request.data,partial=True)
            if request.FILES:
                event.picture = request.FILES['file_field']
            else:
                event.picture = None
            if serializer.is_valid():
                serializer.save()
                return response.Response(serializer.data)
        except Exception as e:
            EventView.handle_error(e)

    @staticmethod
    def create_wallet(event):
        minimum_balance = moneyed.Money(0,'INR')
        maximum_balance = moneyed.Money(0,'INR')
        associated_event = event
        type = 'E'
        return Wallet.objects.create(minimum_balance, maximum_balance, type, 'INR',None, associated_event)

    def post(self, request, access_token, id, *args, **kwargs):
        try:
            user = UserProfileView.get_profile(access_token).user
            if request.FILES:
                file = request.FILES['file_field']
            else:
                file = None
            event = Event.objects.create_event(admin=user,name=request.data['name'],start_date=request.data['start_date'],end_date=request.data['end_date'],picture=file)
            minimum_balance = moneyed.Money(0, 'INR')
            maximum_balance = moneyed.Money(100000, 'INR')
            wallet = Wallet.objects.create_wallet(minimum_balance, maximum_balance, 'E', 'INR', None, event)
            serializer = EventSerializer(event)
            return response.Response(serializer.data)
        except Exception as e:
            EventView.handle_error(e)
