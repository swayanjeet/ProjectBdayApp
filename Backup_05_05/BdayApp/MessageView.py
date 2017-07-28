from BdayApp.serializers import MessageSerializer
from BdayApp.models import UserProfile, BdayAppUser, Message
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MessageView(generics.GenericAPIView):
    model = Message
    serializer_class = MessageSerializer

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    @staticmethod
    def get_message(access_token,id):
        try:
            user = UserProfileView.get_profile(access_token).user
            logger.info(id)
            message = Message.objects.get(pk=id)
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
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            message = MessageView.get_message(access_token,id)
            logger.info(message.message)
            serializer = MessageSerializer(message)
            return response.Response(serializer.data)
        except Exception as e:
            MessageView.handle_error(e)

    def put(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            message = MessageView.get_message(access_token, id)
            logger.info(message.message)
            serializer = MessageSerializer(message, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return response.Response(serializer.data)
        except Exception as e:
            MessageView.handle_error(e)

    def post(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        try:
            message = request.data['message']
            to_field = BdayAppUser.objects.get(id=request.data['to_field'])
            from_field = UserProfileView.get_profile(access_token).user
            friends = UserProfileView.get_profile(access_token).app_friends.all()
            friends_ = UserProfile.objects.get(user=to_field).app_friends.all()
            if to_field in friends:
                logger.info("Dere")
            if from_field in friends_:
                logger.info("not der")
            if to_field in friends and from_field in friends_:
                message = Message.objects.create_message(request.data['message'],
                                                            to_field,
                                                            from_field)
                serializer = MessageSerializer(message)
                return response.Response(serializer.data)
            else:
                raise exceptions.PermissionDenied()
        except Exception as e:
            MessageView.handle_error(e)