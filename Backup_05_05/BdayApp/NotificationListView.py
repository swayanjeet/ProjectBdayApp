from BdayApp.serializers import NotificationSerializer
from BdayApp.models import UserProfile, BdayAppUser, Notification
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions, filters
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NotificationListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('id','message','is_read','creation_date')

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        try:
            user = UserProfileView.get_profile(access_token).user
            notification_list = Notification.objects.filter(associated_user=user)
            return notification_list
        except Notification.DoesNotExist:
            raise exceptions.NotFound("notification list not found")
        except Exception as e:
            NotificationListView.handle_error(e)