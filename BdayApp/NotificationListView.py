import logging
import traceback

from rest_framework import generics
from rest_framework import exceptions, filters

from BdayApp.serializers import NotificationSerializer
from BdayApp.models import Notification
from BdayApp.UserProfileView import UserProfileView



logger = logging.getLogger(__name__)


class NotificationListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('id','message','is_read','creation_date')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        try:
            access_token = self.kwargs['access_token']
            user = UserProfileView.get_profile(access_token).user
            notification_list = Notification.objects.filter(associated_user=user)
            return notification_list
        except Notification.DoesNotExist:
            raise exceptions.NotFound("notification list not found")
        except Exception as e:
            NotificationListView.handle_error(e)