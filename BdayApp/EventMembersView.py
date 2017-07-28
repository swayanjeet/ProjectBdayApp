import logging
import json
import stomp
import time
import Queue
import threading
import traceback

from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status
from rest_framework import exceptions, filters

from BdayApp.serializers import Event, UserSerializer, NotificationSerializer
from BdayApp.models import UserProfile, BdayAppUser, Notification, EventChat, UnreadChatBuffer
from BdayApp.UserProfileView import UserProfileView
from BdayApp.Constants import *

logger = logging.getLogger(__name__)

MAX_THREADS = 10
exitFlag  = 0
queueLock = threading.Lock()


class MultiThreading (threading.Thread):
    def __init__(self, name, q):
        threading.Thread.__init__(self)
        self.name = name
        self.q = q
    def run(self):
        print "Starting " + self.name+"\n"
        send_to_queue(self.name, self.q)
        print "Exiting " + self.name+"\n"

def send_to_queue(threadName,q):
    while not exitFlag:
        queueLock.acquire()
        if not q.empty():
            notification = q.get()
            print "%s processing %s" % (threadName, str(notification))
            conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
            conn.start()
            conn.connect(STOMP_ID, STOMP_PASSWORD, wait=True)
            conn.send(body=json.dumps(notification['data']), destination=notification['destination'])
            logger.info("Sending a message through apollo")
            time.sleep(2)
            logger.info("Message Sent.........Disconnecting")
            conn.disconnect()
            logger.info("Disconnected !!!")
            queueLock.release()
        else:
            queueLock.release()
        time.sleep(1)


class EventMembersView(generics.ListAPIView, generics.RetrieveUpdateDestroyAPIView):

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
    def get_members_list(access_token,id):
        try:
            logger.info("Starting function get_members_list")
            user = UserProfileView.get_profile(access_token).user
            logger.info("user obtained from access token")
            if user in Event.objects.get(pk=id).admin.all() or user in Event.objects.get(pk=id).members.all():
                members_list = Event.objects.get(pk=id).members.all()
                logger.info("member list found for event "+id)
                logger.info("Completing function get_members_list")
                return members_list
            else:
                raise exceptions.PermissionDenied()
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("user does not exist")
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventMembersView.handle_error(e)

    def get(self, request, *args, **kwargs):
        try:
            logger.info("Starting GET method")
            access_token = kwargs['access_token']
            id = kwargs['id']
            logger.info("access token is "+access_token+" event id is "+id)
            admin_list = EventMembersView.get_members_list(access_token,id)
            #admin_list = Event.objects.get(pk=id).admin.all()
            serializer = UserSerializer(admin_list, many=True)
            logger.info("Completing GET method")
            return response.Response(serializer.data)
        except Exception as e:
            EventMembersView.handle_error(e)

    def put(self, request, *args, **kwargs):
        try:
            logger.info("Starting PUT method")
            access_token = kwargs['access_token']
            id = kwargs['id']
            global exitFlag
            exitFlag = 0
            logger.info("access token is "+access_token+" event id is"+id)
            user_profile = UserProfileView.get_profile(access_token)
            user = user_profile.user
            event = Event.objects.get(pk=id)
            logger.info("event obtained from id")
            if user in event.admin.all():
                user_ids = eval(request.data['user_ids'])
                for user_id in user_ids:
                    user_ = BdayAppUser.objects.get(pk=user_id)
                    friends = UserProfileView.get_profile(access_token).app_friends.all()
                    friends_ = UserProfile.objects.get(user=user_).app_friends.all()
                    if user in friends_ and user_ in friends:
                        event.members.add(user_)
                        event.save()
                        chat_buffer = UnreadChatBuffer.objects.create(event=event,user=user_,last_read_chat=None)
                        chat_buffer.save()
                        chat = EventChat.objects.create_event_chat(Event.objects.get(pk=event.id), user_, wish=None,
                                                                   message_field= str(user_.id) + " joined the event",
                                                                   url_field=None,
                                                                   file_field=None, type='CENTER')
                        chat.save()
                        logger.info("added center chat")
                        notification_message = "Your friend "+user_profile.first_name+" added you to event "+event.name
                        notification = Notification.objects.create_notification(notification_message,user_,None, type="NEW_MEMBER_ADDITION",event=event)
                        notification.save()
                        logger.info("added notification message "+notification_message)
                        serializer = NotificationSerializer(notification)
                        conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                        conn.start()
                        conn.connect(STOMP_ID, STOMP_PASSWORD, wait=True)
                        conn.send(body=json.dumps(serializer.data), destination='/topic/notifications_' + str(user_.id))
                        logger.info("Sending a message through apollo")
                        time.sleep(2)
                        logger.info("Message Sent.........Disconnecting")
                        conn.disconnect()
                        logger.info("Disconnected !!!")
                    else:
                        raise exceptions.PermissionDenied()
                    event_members = event.members.all()
                    event_admins = event.admin.all()
                    workQueue = Queue.Queue(10)
                    queueLock.acquire()
                    for member in event_members:
                        if member.id is user_.id:
                            continue
                        notification_message = "Your friend " + UserProfile.objects.get(user=user_).first_name + " joined the event " + event.name
                        notification = Notification.objects.create_notification(notification_message, member, None, type="NEW_MEMBER_JOINED",event=event)
                        notification.save()
                        serializer = NotificationSerializer(notification)
                        workQueue.put({"data": serializer.data, "destination": '/topic/notifications_' + str(member.id)})
                    for admin in event_admins:
                        notification_message = "Your friend " + UserProfile.objects.get(
                            user=user_).first_name + " joined the event " + event.name
                        notification = Notification.objects.create_notification(notification_message, admin, None,
                                                                                type="NEW_MEMBER_JOINED",event=event)
                        notification.save()
                        serializer = NotificationSerializer(notification)
                        workQueue.put(
                            {"data": serializer.data, "destination": '/topic/notifications_' + str(admin.id)})

                    queueLock.release()
                    threads = []
                    for i in range(0, MAX_THREADS):
                        thread = MultiThreading("WORKER " + str(i), workQueue)
                        thread.start()
                        threads.append(thread)
                    while not workQueue.empty():
                        pass

                    # Notify threads it's time to exit
                    exitFlag = 1
                    for t in threads:
                        t.join()
                    logger.info("Sent all notifications")
                logger.info("Completing PUT method")
                return response.Response(status=status.HTTP_202_ACCEPTED)
            else:
                raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventMembersView.handle_error(e)

    def delete(self, request, *args, **kwargs):
        try:
            logger.info("Starting DELETE method")
            access_token = kwargs['access_token']
            global exitFlag
            exitFlag = 0
            id = kwargs['id']
            logger.info("access token is " + access_token + " event id is" + id)
            user = UserProfileView.get_profile(access_token).user
            event = Event.objects.get(pk=id)
            logger.info("event obtained from id")
            if "user_ids" in request.data:
                if user in event.admin.all():
                    user_ids = eval(request.data['user_ids'])
                    for user_id in user_ids:
                        user_ = BdayAppUser.objects.get(pk=user_id)
                        friends = UserProfileView.get_profile(access_token).app_friends.all()
                        friends_ = UserProfile.objects.get(user=user_).app_friends.all()
                        if user in friends_ and user_ in friends:
                            event.members.remove(user_)
                            event.save()
                            members = event.members.all()
                            admins = event.admin.all()
                            workQueue = Queue.Queue(10)
                            queueLock.acquire()
                            for member in members:
                                chat = EventChat.objects.create_event_chat(Event.objects.get(pk=id), user, wish=None,
                                                                           message_field=str(user.id) + " deleted "+str(user_.id)+" from the event",
                                                                           url_field=None, file_field=None,
                                                                           type='CENTER')
                                chat.save()
                                logger.info("added center chat")
                                notification_message = "Admin " + UserProfile.objects.get(
                                    user=user).first_name + " has deleted " + UserProfile.objects.get(user=user_).first_name+" from event "+event.name
                                notification = Notification.objects.create_notification(notification_message, member,
                                                                                        None, type='MEMBER_DELETION_BY_ADMIN',event=event)
                                notification.save()
                                serializer = NotificationSerializer(notification)
                                workQueue.put(
                                    {"data": serializer.data, "destination": '/topic/notifications_' + str(member.id)})
                            for admin in admins:
                                chat = EventChat.objects.create_event_chat(Event.objects.get(pk=id), user, wish=None,
                                                                           message_field=str(user.id) + " deleted " + str(user_.id) + " from the event",
                                                                           url_field=None, file_field=None,
                                                                           type='CENTER')
                                chat.save()
                                logger.info("added center chat")
                                notification_message = "Admin " + UserProfile.objects.get(
                                    user=user).first_name + " has deleted " + UserProfile.objects.get(
                                    user=user_).first_name + " from event " + event.name
                                notification = Notification.objects.create_notification(notification_message, admin,
                                                                                        None,
                                                                                        type='MEMBER_DELETION_BY_ADMIN',event=event)
                                notification.save()
                                serializer = NotificationSerializer(notification)
                                workQueue.put(
                                    {"data": serializer.data, "destination": '/topic/notifications_' + str(admin.id)})

                            queueLock.release()
                            threads = []
                            for i in range(0, MAX_THREADS):
                                thread = MultiThreading("WORKER " + str(i), workQueue)
                                thread.start()
                                threads.append(thread)
                            while not workQueue.empty():
                                pass

                            # Notify threads it's time to exit
                            exitFlag = 1
                            for t in threads:
                                t.join()
                            logger.info("Sent all Notification")
                        else:
                            raise exceptions.PermissionDenied()

                    #event.members.remove(BdayAppUser.objects.get(pk=request.data['user_id']))
                    #event.save()
                    logger.info("Completing DELETE method")
                    return response.Response(status=status.HTTP_202_ACCEPTED)
                else:
                    raise exceptions.PermissionDenied()
            else:
                if user in event.members.all() and user not in event.admin.all():
                    event.members.remove(user)
                    members = event.members.all()
                    admins = event.admin.all()
                    workQueue = Queue.Queue(10)
                    queueLock.acquire()
                    for member in members:
                        event.save()
                        chat = EventChat.objects.create_event_chat(Event.objects.get(pk=event.id), user, wish=None,
                                                               message_field=str(user.id) + "left the event", url_field=None,
                                                               file_field=None, type='CENTER')
                        chat.save()
                        notification_message = "Your friend " + UserProfile.objects.get(user=user).first_name + " left the event " + event.name
                        notification = Notification.objects.create_notification(notification_message, member, None,type='MEMBER_LEAVING_EVENT',event=event)
                        notification.save()
                        serializer = NotificationSerializer(notification)
                        workQueue.put(
                            {"data": serializer.data, "destination": '/topic/notifications_' + str(member.id)})
                    for admin in admins:
                        event.save()
                        chat = EventChat.objects.create_event_chat(Event.objects.get(pk=event.id), user, wish=None,
                                                                   message_field=str(user.id) + "left the event",
                                                                   url_field=None,
                                                                   file_field=None, type='CENTER')
                        chat.save()
                        notification_message = "Your friend " + UserProfile.objects.get(
                            user=user).first_name + " left the event " + event.name
                        notification = Notification.objects.create_notification(notification_message, admin, None,
                                                                                type='MEMBER_LEAVING_EVENT',event=event)
                        notification.save()
                        serializer = NotificationSerializer(notification)
                        workQueue.put(
                            {"data": serializer.data, "destination": '/topic/notifications_' + str(admin.id)})

                    queueLock.release()
                    threads = []
                    for i in range(0, MAX_THREADS):
                        thread = MultiThreading("WORKER " + str(i), workQueue)
                        thread.start()
                        threads.append(thread)
                    while not workQueue.empty():
                        pass
                    # Notify threads it's time to exit
                    exitFlag = 1
                    for t in threads:
                        t.join()
                    logger.info("Sent all Notification")
                    logger.info("Completing DELETE method")
                else:
                    raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventMembersView.handle_error(e)
