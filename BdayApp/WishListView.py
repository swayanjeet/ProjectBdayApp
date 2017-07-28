import logging
import traceback

from rest_framework import generics
from rest_framework import mixins, status, exceptions, filters

from BdayApp.serializers import WishSerializer
from BdayApp.models import UserProfile, BdayAppUser, Wish
from BdayApp.UserProfileView import UserProfileView


logger = logging.getLogger(__name__)

class WishListView(generics.ListAPIView,generics.RetrieveUpdateDestroyAPIView):

    model = Wish
    serializer_class = WishSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('id', 'name', 'website_name', 'creation_date', 'price')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        if self.kwargs['id'].isalnum():
            id = self.kwargs['id']
        else:
            id = None
        wish_list = Wish.objects.none()
        try:
            if id is None:
                user = UserProfileView.get_profile(access_token).user
                wish_list = Wish.objects.filter(user=user)
            else:
                user = BdayAppUser.objects.get(id=id)
                friend_list = UserProfile.objects.get(user=user).app_friends.all()
                friend = UserProfileView.get_profile(access_token).user
                if friend in friend_list:
                    wish_list = Wish.objects.filter(user=user)
                else :
                    raise exceptions.PermissionDenied()
            return wish_list
        except Wish.DoesNotExist:
            raise exceptions.NotFound("wish list doesn't exist")
        except Exception as e:
            WishListView.handle_error(e)