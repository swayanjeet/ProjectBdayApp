import logging
import stomp
import time
import json
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import parsers
from rest_framework import mixins, status, exceptions, filters

from BdayApp.serializers import ChatListSerializer, UnreadChatBufferSerializer
from BdayApp.models import UserProfile, BdayAppUser, EventChat, Event, Wish, UnreadChatBuffer
from BdayApp.UserProfileView import UserProfileView
from BdayApp.SiteParser import URLParser
from BdayApp.Constants import *

logger = logging.getLogger(__name__)


class ChatListView(generics.ListAPIView,generics.CreateAPIView):

    model = EventChat
    parser_classes = (parsers.JSONParser,parsers.MultiPartParser,parsers.FormParser,)
    serializer_class = ChatListSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('user.user_name', 'message_field', 'wish.name', 'wish.price', 'url_field', 'wish.website_name')

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        try:
            logger.info("Starting function get_queryset")
            access_token = self.kwargs['access_token']
            id = self.kwargs['id']
            logger.info("access token is "+access_token+" chat id is "+id)
            user = UserProfile.objects.get(profile_id__exact='1069321953161548').user#UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")
            chat_list = EventChat.objects.filter(event=Event.objects.get(pk=id))
            logger.info("chat id found from chatlist")
            logger.info("Completing function get_queryset")
            return chat_list
        except Event.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except EventChat.DoesNotExist:
            raise exceptions.NotFound("chat list not found")
        except Exception as e:
            ChatListView.handle_error(e)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        access_token = kwargs['access_token']
        event_id = kwargs['id']
        user = UserProfile.objects.get(profile_id__exact='1069321953161548').user#UserProfileView.get_profile(access_token=access_token).user
        data = UnreadChatBuffer.objects.get(event=Event.objects.get(pk=event_id), user=user).last_read_chat
        serializer = ChatListSerializer(queryset, many=True)
        return response.Response(serializer.data)

    def post(self, request, *args, **kwargs):
        try:
            logger.info("Starting POST method")
            access_token = kwargs['access_token']
            id = kwargs['id']
            message_field = None
            url_field = None
            file_field = None
            wish = None
            user_profile = None
            logger.info("access token is "+access_token+" chat id is "+id)
            if "access_token" in request.session:
                user_profile = UserProfile.objects.get(access_token=access_token)
            else:
                user_profile = UserProfileView.get_profile(access_token)
            logger.info("user profile found from access token")
            user = user_profile.user
            event = Event.objects.get(pk=id)
            admins = event.admin.all()
            members = event.members.all()
            if user in admins or user in members:
                if request.data.__contains__('message_field'):
                    logger.info("message field found in chat")
                    message_field = request.data['message_field']
                elif request.data.__contains__('url_field'):
                    logger.info("url field found in chat")
                    url_field = request.data['url_field']
                    url_parser = URLParser(url_field)
                    dict_ = url_parser.parse()
                    wish = Wish.objects.create_wish(url_field, dict_['name'], dict_['website_name'], dict_['website_url'],
                                                    dict_['price'], dict_['picture'], event=event)
                    logger.info("wish created for parsing url field")
                elif request.FILES.__contains__('file_field'):
                    logger.info("file field found in chat")
                    file_field = request.FILES['file_field']
                else:
                    file_field = None
                logger.info(message_field)
                chat = EventChat.objects.create_event_chat(Event.objects.get(pk=id),user,wish,message_field,url_field,file_field)
                chat.save()
                logger.info("Chat created and saved")
                serializer = ChatListSerializer(chat)
                conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                conn.start()
                conn.connect(STOMP_ID, STOMP_PASSWORD, wait=True)
                conn.send(body=json.dumps(serializer.data), destination='/topic/chat_' + str(event.id))
                logger.info("Sending a message through apollo")
                time.sleep(2)
                logger.info("Message Sent.........Disconnecting")
                conn.disconnect()
                logger.info("Disconnected !!!")
                logger.info("Completing function POST method")
                return response.Response(serializer.data)
            else:
                raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except Exception as e:
            ChatListView.handle_error(e)
