import logging
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import status
from rest_framework import exceptions, filters

from BdayApp.serializers import UserSerializer
from BdayApp.models import BdayAppUser
from BdayApp.UserProfileView import UserProfileView

logger = logging.getLogger(__name__)

class FriendListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = BdayAppUser
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('user_name', 'id')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        try:
            logger.info("Starting function get_queryset")
            access_token = self.kwargs['access_token']
            friend_list = UserProfileView.get_profile(access_token).app_friends.all()
            logger.info("Completing function get_queryset")
            return friend_list
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("friend list not found")
        except Exception as e:
            FriendListView.handle_error(e)

    def put(self, request, *args, **kwargs):
        try:
            logger.info("Starting PUT method")
            access_token = kwargs['access_token']
            UserProfileView.get_profile(access_token).\
                app_friends.add(BdayAppUser.objects.get(pk=request.data['user_id']))
            logger.info("Added user to friend list")
            logger.info("Completing PUT method")
            return response.Response(status=status.HTTP_202_ACCEPTED)
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("user with "+request.data['user_id']+" not found")
        except Exception as e:
            FriendListView.handle_error(e)

    def delete(self, request, *args, **kwargs):
        try:
            logger.info("Starting DELETE method")
            access_token = kwargs['access_token']
            UserProfileView.get_profile(access_token).\
                app_friends.remove(BdayAppUser.objects.get(pk=request.data['user_id']))
            logger.info("Completing DELETE method")
            return response.Response(status=status.HTTP_202_ACCEPTED)
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("user with " + request.data['user_id'] + " not found")
        except Exception as e:
            FriendListView.handle_error(e)
