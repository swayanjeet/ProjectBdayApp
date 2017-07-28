from django.db.models import Q
from BdayApp.serializers import EventSerializer, Event
from BdayApp.models import UserProfile
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status
from rest_framework import exceptions, filters
import logging
import json


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class EventListView(generics.ListAPIView):

    model = Event
    serializer_class = EventSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('event_id', 'name')

    def handle_error(self,e):
        logger.error(e)
        raise exceptions.APIException(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        filter_by = self.request.query_params.get('user', None)
        events = Event.objects.none()
        try:
            user = UserProfileView.get_profile(access_token).user
            if filter_by == "admin":
                events = Event.objects.filter(admin=user)
            elif filter_by == "member":
                logger.info("members")
                events = Event.objects.filter(members=user)
            else:
                events = Event.objects.filter(Q(admin=user) | Q(members=user)).distinct()
            return events
        except Event.DoesNotExist:
            raise exceptions.NotFound("No event found")
        except Exception as e:
            EventListView.handle_error(e)


