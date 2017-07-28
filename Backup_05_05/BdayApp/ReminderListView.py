from BdayApp.serializers import ReminderSerializer
from BdayApp.models import UserProfile, BdayAppUser, Reminder
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions, filters
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ReminderListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = Reminder
    serializer_class = ReminderSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('id', 'name', 'creation_date', 'reminder_date')

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        try:
            user = UserProfileView.get_profile(access_token).user
            reminder_list = Reminder.objects.filter(user=user)
            return reminder_list
        except Reminder.DoesNotExist:
            raise exceptions.NotFound("reminder list not found")
        except Exception as e:
            ReminderListView.handle_error(e)