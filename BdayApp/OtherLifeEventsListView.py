import logging
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import status
from rest_framework import exceptions, filters
from rest_framework import parsers

from BdayApp.serializers import OtherLifeEventsSerializer
from BdayApp.models import OtherLifeEvents, UserProfile, Reminder
from BdayApp.UserProfileView import UserProfileView

logger = logging.getLogger(__name__)


class OtherLifeEventsListView(generics.ListAPIView, generics.CreateAPIView, generics.RetrieveUpdateDestroyAPIView):

    model = OtherLifeEvents
    parser_classes = (parsers.JSONParser,parsers.MultiPartParser,parsers.FormParser,)
    serializer_class = OtherLifeEventsSerializer

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        try:
            logger.info("Starting function get_queryset")
            access_token = self.kwargs['access_token']
            logger.info("access token is "+access_token)
            user = UserProfile.objects.get(profile_id__exact='1069321953161548').user#UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")
            other_life_events_list = OtherLifeEvents.objects.filter(user=user)
            logger.info("other life events list found")
            logger.info("Completing function get_queryset")
            return other_life_events_list
        except OtherLifeEvents.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except Exception as e:
            OtherLifeEventsListView.handle_error(e)

    def delete(self, request, *args, **kwargs):
        try:
            logger.info("Starting DELETE method")
            access_token = kwargs['access_token']
            event_id = kwargs['other_life_event_id']
            user = UserProfile.objects.get(
                profile_id__exact='1069321953161548').user  # UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")
            another_life_event = OtherLifeEvents.objects.get(pk=event_id)
            logger.info("life event found from event id")
            if user == another_life_event.user:
                another_life_event.delete()
                return response.Response(status=status.HTTP_202_ACCEPTED)
            else:
                raise exceptions.PermissionDenied()
        except Exception as e:
            OtherLifeEventsListView.handle_error(e)

    def post(self, request, *args, **kwargs):
        try:
            logger.info("Starting POST method")
            access_token = kwargs['access_token']
            required_fields = ['name','date_of_event','type']
            for field in required_fields:
                if not request.data.__contains__(field):
                       raise exceptions.APIException("essential "+field+" not found in post request")
            user_profile = UserProfile.objects.get(
                profile_id__exact='1069321953161548')  # UserProfileView.get_profile(access_token).user
            user = user_profile.user
            logger.info("user found from access token")
            another_life_event = OtherLifeEvents.objects.create(name=request.data['name'],date_of_event=request.data['date_of_event'],type=request.data['type'],user=user)
            another_life_event.save()
            for friend in user_profile.app_friends.all():
                friends_profile = UserProfile.objects.get(user=friend)
                friends_bday_reminder = Reminder.objects.create_reminder(
                    friends_profile.user_name + "'s Life Event",
                    request.data['date_of_event'],
                    friends_profile.user, False, None, user_profile.picture,
                    type='FACEBOOK',
                    reminder_for=user_profile.user
                )
                friends_bday_reminder.save()
            another_life_event_serializer = OtherLifeEventsSerializer(another_life_event)
            return response.Response(another_life_event_serializer.data)
        except Exception as e:
            OtherLifeEventsListView.handle_error(e)