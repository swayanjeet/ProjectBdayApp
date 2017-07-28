from django.db.models import Q
from BdayApp.serializers import MessageSerializer
from BdayApp.models import UserProfile, BdayAppUser, Message
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions, filters
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MessageListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = Message
    serializer_class = MessageSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('to_field.user_name', 'from_field.user_name','id','message','is_read','creation_date')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        raise exceptions.APIException(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        try:

            user = UserProfileView.get_profile(access_token).user
            message_list = Message.objects.filter(Q(from_field=user) | Q(to_field=user))
            return message_list
        except Message.DoesNotExist:
            raise exceptions.NotFound("message list not found")
        except Exception as e:
            MessageListView.handle_error(e)