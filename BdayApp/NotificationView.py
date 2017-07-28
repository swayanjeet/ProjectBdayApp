import logging
import stomp
import json
import time
import traceback

from rest_framework import generics, parsers
from rest_framework import response
from rest_framework import exceptions

from BdayApp.serializers import NotificationSerializer
from BdayApp.models import Notification
from BdayApp.UserProfileView import UserProfileView
from BdayApp.Constants import *

logger = logging.getLogger(__name__)

class NotificationView(generics.CreateAPIView,generics.RetrieveUpdateAPIView):

    model = Notification
    parser_classes = (parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser,)
    serializer_class = NotificationSerializer


    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    @staticmethod
    def get_notification(access_token, id):
        try:
            user = UserProfileView.get_profile(access_token).user
            logger.info("notification id is "+id)
            notification = Notification.objects.get(pk=id)
            if user == notification.associated_user:
                return notification
            else:
                raise exceptions.PermissionDenied()
        except Notification.DoesNotExist:
            raise exceptions.NotFound("notification does not exist")
        except Exception as e:
            NotificationView.handle_error(e)

    def get(self, request, *args, **kwargs):
        try:
            access_token = kwargs['access_token']
            id = kwargs['id']
            notification = NotificationView.get_notification(access_token, id)
            logger.info(notification.message)
            serializer = NotificationSerializer(notification)
            return response.Response(serializer.data)
        except Exception as e:
            NotificationView.handle_error(e)

    def put(self, request, *args, **kwargs):
        try:
            access_token = kwargs['access_token']
            id = kwargs['id']
            notification = NotificationView.get_notification(access_token, id)
            logger.info(notification.message)
            serializer = NotificationSerializer(notification, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return response.Response(serializer.data)
        except Exception as e:
            NotificationView.handle_error(e)

    def post(self, request, *args, **kwargs):
        try:
            access_token = kwargs['access_token']
            message = request.data['message']
            url = None
            user = UserProfileView.get_profile(access_token).user
            # if request.data.__contains__('url'):
            #     url = request.data['url']
            notification = Notification.objects.create_notification(message,user,url)
            notification.save()
            serializer = NotificationSerializer(notification)
            conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
            conn.start()
            conn.connect(STOMP_ID, STOMP_PASSWORD, wait=True)
            conn.send(body=json.dumps(serializer.data), destination='/topic/notifications_' + str(user.id))
            logger.info("Sending a message through apollo")
            time.sleep(2)
            logger.info("Message Sent.........Disconnecting")
            conn.disconnect()
            logger.info("Disconnected !!!")
            return response.Response(serializer.data)
        except Exception as e:
            NotificationView.handle_error(e)



