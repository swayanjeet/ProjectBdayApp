from BdayApp.serializers import UserProfile, UserProfileSerializer, BdayAppUser, BdayAppUsermanager,  Reminder, Notification, NotificationSerializer, Wallet
from BdayApp.Constants import *
from rest_framework import generics
from rest_framework import response, parsers
from rest_framework import mixins, status, exceptions
import moneyed
import facebook
import logging
import json
import datetime
import stomp
import time
import Queue
import threading
import traceback

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


class UserProfileView(generics.GenericAPIView, mixins.UpdateModelMixin,mixins.RetrieveModelMixin):

    model = UserProfile
    parser_classes = (parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser,)
    serializer_class = UserProfileSerializer

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    @staticmethod
    def get_profile(access_token):
        content = dict()
        try:
            #graph = facebook.GraphAPI(access_token=access_token, version='2.8')
            #profile_id = graph.get_object(id='me')['id']
            user_profile = UserProfile.objects.get(profile_id__exact='1069321953161548')#str(profile_id))
            if user_profile.access_token is not access_token:
                user_profile.access_token = access_token
                user_profile.save()
            return user_profile
        except UserProfile.DoesNotExist:
            raise exceptions.NotFound("Profile not found")
        except Exception as e:
            UserProfileView.handle_error(e)

    @staticmethod
    def sync_friends(user_profile):
        try:
            global exitFlag
            exitFlag = 0
            user_friends = user_profile.app_friends.all()
            graph = facebook.GraphAPI(access_token=user_profile.access_token, version='2.8')
            friends_from_facebook = graph.get_connections('me', "friends")
            while True:
                try:
                    for friend in friends_from_facebook['data']:
                        id = friend['id'].encode('utf-8')
                        try:
                            if UserProfile.objects.get(profile_id=id) is not None:
                                friends_profile = UserProfile.objects.get(profile_id=id)
                                if user_profile.user not in friends_profile.app_friends.all():
                                    friends_profile.app_friends.add(user_profile.user)
                                    friends_profile.save()

                                    notification_message = "Your friend "+user_profile.first_name+" joined BdayApp !"
                                    notification = Notification.objects.create_notification(notification_message,friends_profile.user,None,type='NEW_JOINEE')
                                    notification.save()
                                    serializer = NotificationSerializer(notification)
                                    conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                                    conn.start()
                                    conn.connect(STOMP_ID, STOMP_PASSWORD, wait=True)
                                    conn.send(body=json.dumps(serializer.data), destination='/topic/notifications_' + str(friends_profile.user.id))
                                    logger.info("Sending a message through apollo")
                                    time.sleep(2)
                                    logger.info("Message Sent.........Disconnecting")
                                    conn.disconnect()
                                    logger.info("Disconnected !!!")

                                    if friends_profile.birthday is not None:
                                        friends_bday_reminder = Reminder.objects.create_reminder(
                                            friends_profile.user_name + "'s Bday",
                                            datetime.datetime.strptime(
                                                friends_profile.birthday, '%m/%d/%Y'),
                                            user_profile.user, False, None, friends_profile.picture,
                                            type='FACEBOOK',
                                            reminder_for=friends_profile.user
                                        )
                                        friends_bday_reminder.save()
                                if friends_profile.user not in user_profile.app_friends.all():
                                    user_profile.app_friends.add(friends_profile.user)
                                    user_profile.save()

                                    notification_message = "Your friend "+friends_profile.first_name+" joined BdayApp !"
                                    notification = Notification.objects.create_notification(notification_message,user_profile.user,None,type='NEW_JOINEE')
                                    notification.save()
                                    serializer = NotificationSerializer(notification)
                                    conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                                    conn.start()
                                    conn.connect(STOMP_ID, STOMP_PASSWORD, wait=True)
                                    conn.send(body=json.dumps(serializer.data), destination='/topic/notifications_' + str(user_profile.user.id))
                                    logger.info("Sending a message through apollo")
                                    time.sleep(2)
                                    logger.info("Message Sent.........Disconnecting")
                                    conn.disconnect()
                                    logger.info("Disconnected !!!")

                                    if user_profile.birthday is not None:
                                        self_bday_reminder_for_friends = Reminder.objects.create_reminder(
                                            user_profile.user_name + "'s Bday",
                                            datetime.datetime.strptime(
                                                user_profile.birthday,
                                                '%m/%d/%Y'),
                                            friends_profile.user,
                                            False, None,
                                            user_profile.picture,
                                            type='FACEBOOK',
                                            reminder_for=user_profile.user
                                        )
                                        self_bday_reminder_for_friends.save()
                        except UserProfile.DoesNotExist:
                            continue
                    # Attempt to make a request to the next page of data, if it exists.
                    friends_from_facebook = graph.get_connections("me", "friends", after=friends_from_facebook['paging']['cursors']['after'])
                except KeyError:
                    # When there are no more pages (['paging']['next']), break from the
                    # loop and end the script.
                    logger.debug("Break encountered")
                    break
        except Exception as e:
            UserProfileView.handle_error(e)


    def get(self, request, access_token,*args, **kwargs):
        try:
            user_profile = UserProfileView.get_profile(access_token=access_token)
            serializer = UserProfileSerializer(user_profile)
            UserProfileView.sync_friends(user_profile)
            request.session.clear()
            request.session['access_token'] = user_profile.access_token
            logger.info("Completing get method")
            return response.Response(data=serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            UserProfileView.handle_error(e)

    def put(self, request,access_token, *args, **kwargs):
        try:
            user_profile = UserProfileView.get_profile(access_token=access_token)
            serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                if 'birthday' in request.data:
                    reminder = Reminder.objects.create_reminder("My Bday",
                                                                datetime.datetime.strptime(
                                                                    user_profile.birthday,
                                                                    '%m/%d/%Y'),
                                                                user_profile.user,
                                                                False, None,
                                                                user_profile.picture,
                                                                type='FACEBOOK',
                                                                reminder_for=user_profile.user
                                                                )
                    reminder.save()
                    friends = user_profile.app_friends.all()
                    for friend in friends:
                        reminder = Reminder.objects.create_reminder(user_profile.user_name + "'s Bday",
                                                         datetime.datetime.strptime(
                                                             user_profile.birthday,
                                                             '%m/%d/%Y'),
                                                         friend,
                                                         False, None,
                                                         user_profile.picture,
                                                         type='FACEBOOK',
                                                         reminder_for=user_profile.user
                                                         )
                        reminder.save()
                return response.Response(serializer.data)
        except Exception as e:
            UserProfileView.handle_error(e)

    def post(self, request, access_token, *args, **kwargs):
        try:
            global exitFlag
            exitFlag = 0
            user = BdayAppUser.objects.create_user()
            minimum_balance = moneyed.Money(0, 'INR')
            maximum_balance = moneyed.Money(100000, 'INR')
            wallet = Wallet.objects.create_wallet(minimum_balance, maximum_balance, 'U', 'INR', user, None)
            user_profile = UserProfile.objects.create_user_profile(access_token, request.data['profile_type'], user)
            serializer = UserProfileSerializer(user_profile)
            friends = user_profile.app_friends.all()
            total_number_of_friends = 0
            workQueue = Queue.Queue(10)
            queueLock.acquire()

            for friend in friends:
                total_number_of_friends += 1
                notification_message = "Your friend "+user_profile.first_name+" just joined BdayApp ! Gift him !!!"
                notification = Notification.objects.create_notification(notification_message,friend,None)
                notification.save()
                serializer = NotificationSerializer(notification)
                workQueue.put({"data":serializer.data,"destination":'/topic/notifications_' + str(friend.id)})
            queueLock.release()
            threads = []
            for i in range(0,MAX_THREADS):
                thread = MultiThreading("WORKER "+str(i),workQueue)
                thread.start()
                threads.append(thread)
            while not workQueue.empty():
                pass

            # Notify threads it's time to exit

            exitFlag = 1
            for t in threads:
                t.join()
            print "Sent all Notification"

                # conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                # conn.start()
                # conn.connect('admin', 'password', wait=True)
                # conn.send(body=json.dumps(serializer.data), destination='/topic/notifications_' + str(friend.id))
                # logger.info("Sending a message through apollo")
                # time.sleep(2)
                # logger.info("Message Sent.........Disconnecting")
                # conn.disconnect()
                # logger.info("Disconnected !!!")

            logger.info("Total friends"+str(total_number_of_friends))
            if total_number_of_friends > 0 :
                notification_message = "Your have"+ str(total_number_of_friends) +" friends on Bdayapp. Kudos !!"
                notification = Notification.objects.create_notification(notification_message,user_profile.user,None)
                notification.save()
                serializer = NotificationSerializer(notification)
                conn = stomp.Connection([(STOMP_SERVER_URL, STOMP_PORT)])
                conn.start()
                conn.connect(STOMP_ID, STOMP_PASSWORD, wait=True)
                conn.send(body=json.dumps(serializer.data), destination='/topic/notifications_' + str(user_profile.user.id))
                logger.info("Sending a message through apollo")
                time.sleep(2)
                logger.info("Message Sent.........Disconnecting")
                conn.disconnect()
                logger.info("Disconnected !!!")

            return response.Response(serializer.data)
        except Exception as e:
            UserProfileView.handle_error(e)
