import logging
import traceback
from django.db.models import Q

from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions, filters

from BdayApp.serializers import MessageSerializer
from BdayApp.models import UserProfile, BdayAppUser, Message
from BdayApp.UserProfileView import UserProfileView

logger = logging.getLogger(__name__)

class MessageListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = Message
    serializer_class = MessageSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('to_field.user_name', 'from_field.user_name','id','message','is_read','creation_date')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        try:
            logger.info("Starting function get_queryset")
            access_token = self.kwargs['access_token']
            user = UserProfileView.get_profile(access_token).user
            message_list = Message.objects.filter(Q(from_field=user) | Q(to_field=user))
            logger.info("Completing function get_queryset")
            return message_list
        except Message.DoesNotExist:
            raise exceptions.NotFound("message list not found")
        except Exception as e:
            MessageListView.handle_error(e)