import logging
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status
from rest_framework import exceptions, filters

from BdayApp.serializers import Event, UserSerializer
from BdayApp.models import UserProfile, BdayAppUser, Notification, UnreadChatBuffer
from BdayApp.UserProfileView import UserProfileView


logger = logging.getLogger(__name__)

class EventAdminView(generics.ListAPIView,generics.UpdateAPIView):

    model = BdayAppUser
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('user_name', 'id')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    @staticmethod
    def get_admin_list(access_token,id):
        try:
            logger.info("Starting function get_admin_list")
            user = UserProfileView.get_profile(access_token).user
            if user in Event.objects.get(pk=id).admin.all() or user in Event.objects.get(pk=id).members.all():
                admin_list = Event.objects.get(pk=id).admin.all()
                logger.info("admin list retrieved")
                logger.info("Completing function get_admin_list")
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
        try:
            logger.info("Starting get_queryset method")
            access_token = self.kwargs['access_token']
            id = self.kwargs['id']
            logger.info("access token is "+access_token+" event id is "+id)
            admin_list = BdayAppUser.objects.none()
            admin_list = EventAdminView.get_admin_list(access_token, id)
            logger.info("Completing get_queryset method")
            return admin_list
        except Exception as e:
            EventAdminView.handle_error(e)

    def put(self, request, *args, **kwargs):
        try:
            logger.info("Starting PUT method")
            access_token = kwargs['access_token']
            id = kwargs['id']
            logger.info("access token is "+access_token+" event id for adding member is "+id)
            user = UserProfileView.get_profile(access_token).user
            event = Event.objects.get(pk=id)
            logger.info("event found with id "+id)
            if user in event.admin.all():
                user_ = BdayAppUser.objects.get(pk=request.data['user_id'])
                friends = UserProfileView.get_profile(access_token).app_friends.all()
                friends_ = UserProfile.objects.get(user=user_).app_friends.all()
                if user in friends_ and user_ in friends:
                    logger.info("Both the users are friend of each other")
                    event.admin.add(user_)
                    event.save()
                    chat_buffer = UnreadChatBuffer.objects.create(event=event, user=user, last_read_chat=None)
                    chat_buffer.save()
                    notification_message = "Your friend " + UserProfile.objects.get(user=user).first_name + " made you admin of the event " + event.name
                    notification = Notification.objects.create_notification(notification_message, user_, None,
                                                                            type="ADMIN_ADDITION")
                    notification.save()
                    logger.info("Completing PUT method")
                    return response.Response(status=status.HTTP_202_ACCEPTED)
                else:
                    raise exceptions.PermissionDenied()    
            else:
                raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventAdminView.handle_error(e)