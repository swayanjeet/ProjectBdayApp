from BdayApp.serializers import ChatListSerializer
from BdayApp.models import UserProfile, BdayAppUser, EventChat, Event, Wish
from BdayApp.UserProfileView import UserProfileView
from BdayApp.SiteParser import URLParser
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions, filters
import logging
import stomp
import time
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

STOMP_SERVER_URL = '35.162.117.56'
STOMP_PORT = 61613

class ChatListView(generics.ListAPIView,generics.CreateAPIView):

    model = EventChat
    serializer_class = ChatListSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields =('user.user_name', 'message_field', 'wish.name', 'wish.price', 'url_field', 'wish.website_name')

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    def get_queryset(self):
        access_token = self.kwargs['access_token']
        id = self.kwargs['id']
        try:
            user = UserProfileView.get_profile(access_token).user
            chat_list = EventChat.objects.filter(event = Event.objects.get(pk=id))
            return chat_list
        except Event.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except EventChat.DoesNotExist:
            raise exceptions.NotFound("chat list not found")
        except Exception as e:
            ChatListView.handle_error(e)

    def post(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        message_field = None
        url_field = None
        file_field = None
        wish = None
        try:
            user_profile = None
            if "access_token" in request.session:
                user_profile = UserProfile.objects.get(access_token=access_token)
            else:
                raise exceptions.PermissionDenied()
            user = user_profile.user
            event = Event.objects.get(pk=id)
            admins = event.admin.all()
            members = event.members.all()
            if user in admins or user in members:
                if request.data.__contains__('message_field'):
                    message_field = request.data['message_field']
                    logger.info(message_field)
                elif request.data.__contains__('url_field'):
                    url_field = request.data['url_field']
                    url_parser = URLParser(url_field)
                    dict_ = url_parser.parse()
                    wish = Wish.objects.create_wish(url_field, dict_['name'], dict_['website_name'], dict_['website_url'],
                                                    dict_['price'], dict_['picture'], user)
                elif request.FILES.__contains__('file_field'):
                    file_field = request.FILES['file_field']
                else:
                    message_field = None
                logger.info(message_field)
                chat = EventChat.objects.create_event_chat(Event.objects.get(pk=id),user,wish,message_field,url_field,file_field)
                chat.save()
                serializer = ChatListSerializer(chat)
                conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                conn.start()
                conn.connect('admin', 'password', wait=True)
                conn.send(body=json.dumps(serializer.data), destination='/topic/chat_' + str(event.id))
                logger.info("Sending a message through apollo")
                time.sleep(2)
                logger.info("Message Sent.........Disconnecting")
                conn.disconnect()
                logger.info("Disconnected !!!")
                return response.Response(serializer.data)
            else:
                raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except Exception as e:
            ChatListView.handle_error(e)
