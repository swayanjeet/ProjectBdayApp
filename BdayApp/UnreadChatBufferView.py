import logging
import traceback
from rest_framework import generics
from rest_framework import response, parsers
from rest_framework import mixins, status, exceptions, filters
from BdayApp.serializers import UnreadChatBufferSerializer
from BdayApp.models import UserProfile, BdayAppUser, EventChat, Event, Wish, UnreadChatBuffer
from BdayApp.UserProfileView import UserProfileView



logger = logging.getLogger(__name__)

class UnreadChatBufferView(generics.UpdateAPIView, generics.RetrieveAPIView):

    model = UnreadChatBuffer
    parser_classes = (parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser,)
    serializer_class = UnreadChatBufferSerializer


    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get(self, request, *args, **kwargs):
        try:
            access_token = kwargs['access_token']
            event_id = kwargs['event_id']
            user = UserProfileView.get_profile(access_token=access_token).user
            data = UnreadChatBuffer.objects.get(event=Event.objects.get(pk=event_id),user=user)
            serializer = UnreadChatBufferSerializer(data)
            return response.Response(serializer.data)
        except Event.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("user not found")
        except Exception as e:
            UnreadChatBufferView.handle_error(e)

    def put(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        try:
            access_token = kwargs['access_token']
            event_id = kwargs['event_id']
            last_read_chat = EventChat.objects.get(pk=request.data['last_read_chat_id'])
            user = UserProfileView.get_profile(access_token=access_token).user
            data = UnreadChatBuffer.objects.get(event=Event.objects.get(pk=event_id),user=user)
            data.last_read_chat = last_read_chat
            data.save()
            serializer = UnreadChatBufferSerializer(data)
            return response.Response(serializer.data)
        except Event.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("user not found")
        except EventChat.DoesNotExist:
            raise exceptions.NotFound("chat does not exist")
        except Exception as e:
            UnreadChatBufferView.handle_error(e)