from BdayApp.serializers import EventSerializer, Event, UserSerializer
from BdayApp.models import UserProfile, BdayAppUser
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status
from rest_framework import exceptions, filters
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FriendListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = BdayAppUser
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('user_name', 'id')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        raise exceptions.APIException(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        try:
            friend_list = UserProfileView.get_profile(access_token).app_friends.all()
            return friend_list
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("friend list not found")
        except Exception as e:
            FriendListView.handle_error(e)

    def put(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        try:
            UserProfileView.get_profile(access_token).\
                app_friends.add(BdayAppUser.objects.get(pk=request.data['user_id']))
            return response.Response(status=status.HTTP_202_ACCEPTED)
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("friend list not found")
        except Exception as e:
            FriendListView.handle_error(e)

    def delete(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        try:
            UserProfileView.get_profile(access_token).\
                app_friends.remove(BdayAppUser.objects.get(pk=request.data['user_id']))
            return response.Response(status=status.HTTP_202_ACCEPTED)
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("friend list not found")
        except Exception as e:
            FriendListView.handle_error(e)
