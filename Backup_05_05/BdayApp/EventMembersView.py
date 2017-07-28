from BdayApp.serializers import EventSerializer, Event, UserSerializer, NotificationSerializer, EventChat, UnreadChatBuffer
from BdayApp.models import UserProfile, BdayAppUser, Notification
from BdayApp.UserProfileView import UserProfileView
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status
from rest_framework import exceptions, filters
import logging
import json
import stomp
import time
import Queue
import threading


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

STOMP_SERVER_URL = '35.162.74.72'
STOMP_PORT = 61613
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
            conn.connect('admin', 'password', wait=True)
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
        raise exceptions.APIException(e)

    @staticmethod
    def get_members_list(access_token,id):
        try:
            user = UserProfileView.get_profile(access_token).user
            if user in Event.objects.get(pk=id).admin.all() or user in Event.objects.get(pk=id).members.all():
                members_list = Event.objects.get(pk=id).members.all()
                logger.info(members_list)
                return members_list
            else:
                raise exceptions.PermissionDenied()
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("admin list does not exist")
        except Event.DoesNotExist:
            raise exceptions.NotFound("event list does not exist")
        except Exception as e:
            EventMembersView.handle_error(e)

    def get(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        admin_list = None
        try:
            admin_list = EventMembersView.get_members_list(access_token,id)
            #admin_list = Event.objects.get(pk=id).admin.all()
            serializer = UserSerializer(admin_list, many=True)
            return response.Response(serializer.data)
        except Exception as e:
            EventMembersView.handle_error(e)

    def put(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            user_profile = UserProfileView.get_profile(access_token)
            user = user_profile.user
            event = Event.objects.get(pk=id)
            if user in event.admin.all():
                user_ids = eval(request.data['user_ids'])
                for user_id in user_ids:
                    user_ = BdayAppUser.objects.get(pk=user_id)
                    friends = UserProfileView.get_profile(access_token).app_friends.all()
                    friends_ = UserProfile.objects.get(user=user_).app_friends.all()
                    if user in friends_ and user_ in friends:
                        event.members.add(user_)
                        UnreadChatBuffer.objects.create(event=event,user=user_,last_read_chat=None)
                        chat = EventChat.objects.create_event_chat(Event.objects.get(pk=event.id), user_, wish=None,
                                                                   message_field=user_.id + "joined the event",
                                                                   url_field=None,
                                                                   file_field=None, type='CENTER')
                        chat.save()
                        notification_message = "Your friend "+user_profile.first_name+" added you to event "+event.name
                        notification = Notification.objects.create_notification(notification_message,user_,None)
                        notification.save()
                        serializer = NotificationSerializer(notification)
                        conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                        conn.start()
                        conn.connect('admin', 'password', wait=True)
                        conn.send(body=json.dumps(serializer.data), destination='/topic/notifications_' + str(user_.id))
                        logger.info("Sending a message through apollo")
                        time.sleep(2)
                        logger.info("Message Sent.........Disconnecting")
                        conn.disconnect()
                        logger.info("Disconnected !!!")
                    else:
                        raise exceptions.PermissionDenied()
                event.save()
                event_members = event.members
                workQueue = Queue.Queue(10)
                queueLock.acquire()
                for member in event_members:
                    notification_message = "Your friend " + UserProfile.objects.get(user=user_).first_name + " joined the event " + event.name
                    notification = Notification.objects.create_notification(notification_message, member, None, type="NEW_JOINEE")
                    notification.save()
                    serializer = NotificationSerializer(notification)
                    workQueue.put({"data": serializer.data, "destination": '/topic/notifications_' + str(member.id)})
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
                print "Sent all Notification"
                return response.Response(status=status.HTTP_202_ACCEPTED)
            else:
                raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventMembersView.handle_error(e)

    def delete(self, request, *args, **kwargs):
        access_token = kwargs['access_token']
        id = kwargs['id']
        try:
            user = UserProfileView.get_profile(access_token).user
            event = Event.objects.get(pk=id)
            if "user_ids" in request['data']:
                if user in event.admin.all():
                    user_ids = eval(request.data['user_ids'])
                    for user_id in user_ids:
                        user_ = BdayAppUser.objects.get(pk=user_id)
                        friends = UserProfileView.get_profile(access_token).app_friends.all()
                        friends_ = UserProfile.objects.get(user=user_).app_friends.all()
                        if user in friends_ and user_ in friends:
                            event.members.remove(user_)
                            members = event.members
                            workQueue = Queue.Queue(10)
                            queueLock.acquire()
                            for member in members:
                                chat = EventChat.objects.create_event_chat(Event.objects.get(pk=id), user, wish=None,
                                                                           message_field=user.id + " deleted "+user_.id+" from the event",
                                                                           url_field=None, file_field=None,
                                                                           type='CENTER')
                                chat.save()
                                notification_message = "Admin " + UserProfile.objects.get(
                                    user=user).first_name + " has deleted " + UserProfile.objects.get(user=user_).first_name+" from event "+event.name
                                notification = Notification.objects.create_notification(notification_message, member,
                                                                                        None, type='ADMIN_DELETED_MEMBERS')
                                notification.save()
                                serializer = NotificationSerializer(notification)
                                workQueue.put(
                                    {"data": serializer.data, "destination": '/topic/notifications_' + str(member.id)})
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
                            print "Sent all Notification"
                        else:
                            raise exceptions.PermissionDenied()
                    event.save()
                    #event.members.remove(BdayAppUser.objects.get(pk=request.data['user_id']))
                    #event.save()
                    return response.Response(status=status.HTTP_202_ACCEPTED)
                else:
                    raise exceptions.PermissionDenied()
            else:
                if user in event.members.all() and user not in event.admin.all():
                    event.members.remove(user)
                    event.save()
                    chat = EventChat.objects.create_event_chat(Event.objects.get(pk=event.id), user, wish=None,
                                                               message_field=user.id + "left the event", url_field=None,
                                                               file_field=None, type='CENTER')
                    chat.save()
                    members = event.members
                    workQueue = Queue.Queue(10)
                    queueLock.acquire()
                    for member in members:

                        notification_message = "Your friend " + UserProfile.objects.get(user=user).first_name + " left the event " + event.name
                        notification = Notification.objects.create_notification(notification_message, member, url=None, type='MEMBER_LEAVING_EVENT')
                        notification.save()
                        serializer = NotificationSerializer(notification)
                        workQueue.put(
                            {"data": serializer.data, "destination": '/topic/notifications_' + str(member.id)})
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
                    print "Sent all Notification"
                else:
                    raise exceptions.PermissionDenied()
        except Event.DoesNotExist:
            raise exceptions.NotFound("event does not exist")
        except Exception as e:
            EventMembersView.handle_error(e)