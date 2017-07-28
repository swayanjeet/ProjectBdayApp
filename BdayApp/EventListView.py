import traceback
import logging
import json
from django.db.models import Q

from rest_framework import generics, response
from rest_framework import exceptions, filters

from BdayApp.serializers import EventSerializer, Event, UnreadChatBufferSerializer
from BdayApp.UserProfileView import UserProfileView
from BdayApp.models import UserProfile, UnreadChatBuffer

logger = logging.getLogger(__name__)


class EventListView(generics.ListAPIView):

    model = Event
    serializer_class = EventSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('event_id', 'name')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        try:
            logger.info("Starting function get_queryset")
            access_token = self.kwargs['access_token']
            filter_by = self.request.query_params.get('user', None)
            events = Event.objects.none()
            logger.info("access token is "+access_token+" user is "+str(filter_by))
            user = UserProfile.objects.get(profile_id__exact='1069321953161548').user #UserProfileView.get_profile(access_token).user
            logger.info("user obtained from access token")
            if filter_by == "admin":
                events = Event.objects.filter(admin=user)
                logger.info("events obtained in which user is admin")
            elif filter_by == "member":
                events = Event.objects.filter(members=user)
                logger.info("events obtained in which user is member")
            else:
                events = Event.objects.filter(Q(admin=user) | Q(members=user)).distinct()
                logger.info("events obtained in which user is admin as well as user")
            logger.info("Completing function get_queryset")
            return events
        except Event.DoesNotExist:
            raise exceptions.NotFound("No event found EventListView")
        except Exception as e:
            EventListView.handle_error(e)



