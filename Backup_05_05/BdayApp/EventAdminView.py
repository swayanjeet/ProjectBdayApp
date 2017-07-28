from django.db.models import Q
from BdayApp.serializers import EventSerializer, Event, UserSerializer
from BdayApp.models import UserProfile, BdayAppUser
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status
from rest_framework import exceptions, filters
import logging
import json
import facebook

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class EventAdminView(generics.ListAPIView,generics.UpdateAPIView):

    model = BdayAppUser
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('user_name', 'id')

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    @staticmethod
    def get_admin_list(access_token,id):
        try:
            user = UserProfileView.get_profile(access_token).user
            if user in Event.objects.get(pk=id).admin.all() or user in Event.objects.get(pk=id).members.all():
                admin_list = Event.objects.get(pk=id).admin.all()
                logger.info(admin_list)
                return admin_list
            else:
                raise exceptions.PermissionDenied()
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("admin list does not exist")
        except Event.DoesNotExist:
            raise exceptions.NotFound("event list does not exist")
        except Exception as e:
            EventAdminView.handle_error(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        id = self.kwargs['id']
        admin_list = BdayAppUser.objects.none()
        try:
            admin_list = EventAdminView.get_admin_list(access_token,id)
            #admin_list = Event.objects.get(pk=id).admin.all()
            return admin_list
        except Exception as e:
            EventAdminView.handle_error(e)

    def put(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            user = UserProfileView.get_profile(access_token).user
            event = Event.objects.get(pk=id)
            if user in event.admin.all():
                user_ = BdayAppUser.objects.get(pk=request.data['user_id'])
                friends = UserProfileView.get_profile(access_token).app_friends.all()
                friends_ = UserProfile.objects.get(user=user_).app_friends.all()
                if user in friends_ and user_ in friends:
                    event.admin.add(user_)
                    event.save()
                    return response.Response(status=status.HTTP_202_ACCEPTED)
                else:
                    raise exceptions.PermissionDenied()    
            else:
                raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventAdminView.handle_error(e)