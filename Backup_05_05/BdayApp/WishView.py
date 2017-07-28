from BdayApp.serializers import WishSerializer
from BdayApp.models import UserProfile, BdayAppUser, Wish
from BdayApp.UserProfileView import UserProfileView
from BdayApp.SiteParser import URLParser
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WishView(generics.GenericAPIView):

    model = Wish
    serializer_class = WishSerializer

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    @staticmethod
    def get_wish(access_token, id):
        try:
            user = UserProfileView.get_profile(access_token).user
            logger.info(id)
            wish = Wish.objects.get(pk=id)
            logger.info(wish.url)
            if user == wish.user:
                return wish
            else:
                raise exceptions.PermissionDenied()
        except Wish.DoesNotExist:
            raise exceptions.NotFound("Wish does not exist")
        except Exception as e:
            WishView.handle_error(e)

    def get(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            wish = WishView.get_wish(access_token,id)
            logger.info(wish.url)
            serializer = WishSerializer(wish)
            return response.Response(serializer.data)
        except Exception as e:
            WishView.handle_error(e)

    def put(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            wish = WishView.get_wish(access_token, id)
            logger.info(wish.url)
            serializer = WishSerializer(wish, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return response.Response(serializer.data)
        except Exception as e:
            WishView.handle_error(e)

    def post(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        try:
            url = request.data['url']
            user = UserProfileView.get_profile(access_token).user
            url_parser = URLParser(url)
            dict_ = url_parser.parse()
            if dict_['status_code'] is not 200:
                raise exceptions.APIException(e)
            wish = Wish.objects.create_wish(url, dict_['name'], dict_['website_name'], dict_['website_url'],dict_['price'],dict_['picture'],user)
            serializer = WishSerializer(wish)
            return response.Response(serializer.data)
        except Exception as e:
            WishView.handle_error(e)

    def delete(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            user = UserProfileView.get_profile(access_token).user
            wish = Wish.objects.get(pk=id)
            if user == wish.user:
                wish.delete()
                return response.Response(status=status.HTTP_202_ACCEPTED)
            else:
                raise exceptions.PermissionDenied()
        except Wish.DoesNotExist:
            raise exceptions.NotFound("Wish does not exist")
        except Exception as e:
            WishView.handle_error(e)



