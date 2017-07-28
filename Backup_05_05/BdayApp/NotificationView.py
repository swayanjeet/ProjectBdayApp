from BdayApp.serializers import NotificationSerializer
from BdayApp.models import UserProfile, BdayAppUser, Notification
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions
import logging
import stomp
import json
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

STOMP_SERVER_URL = '35.162.117.56'
STOMP_PORT = 61613


class NotificationView(generics.GenericAPIView):

    model = Notification
    serializer_class = NotificationSerializer

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    @staticmethod
    def get_notification(access_token,id):
        try:
            user = UserProfileView.get_profile(access_token).user
            logger.info(id)
            notification = Notification.objects.get(pk=id)
            logger.info(notification.message)
            if user == notification.associated_user:
                return notification
            else:
                raise exceptions.PermissionDenied()
        except Notification.DoesNotExist:
            raise exceptions.NotFound("notification does not exist")
        except Exception as e:
            NotificationView.handle_error(e)

    def get(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            notification = NotificationView.get_notification(access_token,id)
            logger.info(notification.message)
            serializer = NotificationSerializer(notification)
            return response.Response(serializer.data)
        except Exception as e:
            NotificationView.handle_error(e)

    def put(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            notification = NotificationView.get_notification(access_token, id)
            logger.info(notification.message)
            serializer = NotificationSerializer(notification, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return response.Response(serializer.data)
        except Exception as e:
            NotificationView.handle_error(e)

    def post(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        try:
            message = request.data['message']
            url = None
            user = UserProfileView.get_profile(access_token).user
            if request.data.__contains__('url'):
                url = request.data['url']
            notification = Notification.objects.create_notification(message,user,url)
            notification.save()
            serializer = NotificationSerializer(notification)
            conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
            conn.start()
            conn.connect('admin', 'password', wait=True)
            conn.send(body=json.dumps(serializer.data), destination='/topic/notifications_' + str(user.id))
            logger.info("Sending a message through apollo")
            time.sleep(2)
            logger.info("Message Sent.........Disconnecting")
            conn.disconnect()
            logger.info("Disconnected !!!")
            return response.Response(serializer.data)
        except Exception as e:
            NotificationView.handle_error(e)



