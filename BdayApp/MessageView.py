import logging
import json
import stomp
import time
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import parsers, status, exceptions

from BdayApp.serializers import MessageSerializer
from BdayApp.models import UserProfile, BdayAppUser, Message
from BdayApp.UserProfileView import UserProfileView
from BdayApp.Constants import *

logger = logging.getLogger(__name__)

class MessageView(generics.RetrieveUpdateAPIView,generics.CreateAPIView):

    model = Message
    parser_classes = (parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser,)
    serializer_class = MessageSerializer

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    @staticmethod
    def get_message(access_token,id):
        try:
            logger.info("Starting function get_message")
            user = UserProfileView.get_profile(access_token).user
            message = Message.objects.get(pk=id)
            logger.info("message found with id "+id)
            logger.info(message.message)
            if user == message.to_field or user == message.from_field:
                return message
            else:
                return response.Response(status=status.HTTP_401_UNAUTHORIZED)
        except Message.DoesNotExist:
            raise exceptions.NotFound("message does not exist")
        except Exception as e:
            MessageView.handle_error(e)

    def get(self, request, *args, **kwargs):
        try:
            access_token = kwargs['access_token']
            id = kwargs['id']
            message = MessageView.get_message(access_token,id)
            logger.info(message.message)
            serializer = MessageSerializer(message)
            return response.Response(serializer.data)
        except Exception as e:
            MessageView.handle_error(e)

    def put(self, request, *args, **kwargs):
        try:
            access_token = kwargs['access_token']
            id = kwargs['id']
            message = MessageView.get_message(access_token, id)
            logger.info(message.message)
            serializer = MessageSerializer(message, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return response.Response(serializer.data)
        except Exception as e:
            MessageView.handle_error(e)

    def post(self, request, *args, **kwargs):
        try:
            message = request.data['message']
            access_token = kwargs['access_token']
            to_field = BdayAppUser.objects.get(id=request.data['to_field'])
            from_field = UserProfileView.get_profile(access_token).user
            friends = UserProfileView.get_profile(access_token).app_friends.all()
            friends_ = UserProfile.objects.get(user=to_field).app_friends.all()
            if to_field in friends and from_field in friends_:
                message = Message.objects.create_message(request.data['message'],
                                                            to_field,
                                                            from_field)
                message.save()
                serializer = MessageSerializer(message)
                conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                conn.start()
                conn.connect(STOMP_ID, STOMP_PASSWORD, wait=True)
                conn.send(body=json.dumps(serializer.data), destination='/topic/message_' + str(to_field.id))
                logger.info("Sending a message through apollo")
                time.sleep(2)
                logger.info("Message Sent.........Disconnecting")
                conn.disconnect()
                logger.info("Disconnected !!!")
                return response.Response(serializer.data)
            else:
                raise exceptions.PermissionDenied()
        except Exception as e:
            MessageView.handle_error(e)