import logging
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions, filters

from BdayApp.serializers import ReminderSerializer
from BdayApp.models import Reminder, UserProfile
from BdayApp.UserProfileView import UserProfileView

logger = logging.getLogger(__name__)


class ReminderListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = Reminder
    serializer_class = ReminderSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('id', 'name', 'creation_date', 'reminder_date')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        try:
            user = UserProfile.objects.get(profile_id__exact='1069321953161548').user#UserProfileView.get_profile(access_token).user
            reminder_list = Reminder.objects.filter(user=user)
            return reminder_list
        except Reminder.DoesNotExist:
            raise exceptions.NotFound("reminder list not found")
        except Exception as e:
            ReminderListView.handle_error(e)
