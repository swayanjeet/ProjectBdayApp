import stomp
import logging
import datetime
import json
import facebook
import Checksum
import moneyed
import random
import time
import Queue
import threading

from django.http import HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q

from BdayApp.models import BdayAppUser, BdayAppUsermanager, UserProfile, UserProfileManager, Wallet, Transaction, Event, Notification, Category, SubCategory, GiftStore, OtherLifeEvents, Wish
from django.utils import timezone
from BdayApp.UserProfileView import UserProfileView
from BdayApp.serializers import NotificationSerializer
from BdayApp.serializers import UserSerializer
from BdayApp.print_queryset import dprint, make_object
from BdayApp.Constants import *


logger = logging.getLogger(__name__)
MERCHANT_KEY = 'fs6lxL&StfY4ZTwL'
MAX_THREADS = 10
exitFlag = 0
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
            conn.send(body=json.dumps(notification['ss']), destination=notification['destination'])
            logger.info("Sending a message through apollo")
            time.sleep(2)
            logger.info("Message Sent.........Disconnecting")
            conn.disconnect()
            logger.info("Disconnected !!!")
            queueLock.release()
        else:
            queueLock.release()
        time.sleep(1)


def index(request):
    return HttpResponse("Hello World")


def send_notification_for_date(request):
    error = {}
    success = {}
    if "date" not in request.GET:
        error["details"] = "invalid parameters"
        return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))
    date = request.GET["date"]
    user_profiles = UserProfile.objects.filter(birthday__contains=date)
    for profile in user_profiles:
        message = "Team Bdayapp wishes you a very happy birthday"
        url = None
        user = profile.user
        notification = Notification.objects.create_notification(message, user, url, type=None)
        notification.save()
    success["details"] = "success"
    return HttpResponse(status=200, content_type="application/json", content=json.dumps(success))


def send_notification_to_friends_for_events(request):
    error = {}
    success = {}
    if "days_before_event" not in request.GET:
        error["details"] = "invalid parameters"
        return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))
    days_before_event = request.GET["days_before_event"]
    added_date_time = datetime.datetime.now() + datetime.timedelta(days=int(days_before_event))
    search_string = str(added_date_time.month)+"/"+str(added_date_time.day)
    print search_string
    user_profiles = UserProfile.objects.filter(birthday__contains=search_string)
    for profile in user_profiles:
        if profile.birthday is None or profile.address is None or profile.phone_number is None:
            message = "Complete your profile so that your friends can gift you"
            url = None
            user = profile.user
            type = "PROFILE_COMPLETION"
            notification = Notification.objects.create_notification(message, user, url, type=type)
            notification.save()
        friends = profile.app_friends.all()
        for friend in friends:
            message = "Your friend "+profile.first_name+" has birthday on "+added_date_time.strftime("%d %b")+". Gift him."
            print message
            url = None
            user = friend
            type = "FRIENDS_EVENT_REMINDER"
            event_reminder_type = "BIRTHDAY"
            event_for_user = profile.user
            notification = Notification.objects.create_notification(message, friend, url, type=type, event_reminder_type=event_reminder_type, event_for_user=event_for_user)
            notification.save()
    success["details"] = "success"
    return HttpResponse(status=200, content_type="application/json", content=json.dumps(success))

def send_notification_for_wishlist(request):
    error = {}
    success = {}
    if "days_before_event" not in request.GET or "last_wish_list_updated_interval" not in request.GET:
        error["details"] = "invalid parameters"
        return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))
    days_before_event = request.GET["days_before_event"]
    last_wish_list_updated_interval = request.GET["last_wish_list_updated_interval"]
    added_date_time = datetime.datetime.now() + datetime.timedelta(days=int(days_before_event))
    search_string = str(added_date_time.month)+"/"+str(added_date_time.day)
    user_profiles = UserProfile.objects.filter(birthday__contains=search_string)
    other_life_events = OtherLifeEvents.objects.filter(date_of_event_month=added_date_time.month, date_of_event_day=added_date_time.day)

    for profile in user_profiles:
        last_wish = Wish.objects.filter(user=profile.user).first()
        last_wish_creation_date_after_adding_time = last_wish.creation_date + datetime.timedelta(days=int(last_wish_list_updated_interval))
        if last_wish_creation_date_after_adding_time < timezone.now():
            message = "Update your wishlist so that your friends can gift you for your birthday"
            url = None
            user = profile.user
            type = "WISH_LIST_COMPLETION"
            notification = Notification.objects.create_notification(message, user, url, type=type)
            notification.save()
    for life_event in other_life_events:
        last_wish = Wish.objects.filter(user=life_event.user).first()
        last_wish_creation_date_after_adding_time = last_wish.creation_date + datetime.timedelta(days=int(last_wish_list_updated_interval))

        if last_wish_creation_date_after_adding_time < timezone.now():
            message = "Update your wishlist so that your friends can gift you for your "+life_event.type
            url = None
            user = life_event.user
            type = "WISH_LIST_COMPLETION"
            notification = Notification.objects.create_notification(message, user, url, type=type)
            notification.save()
    success["details"] = "success"
    return HttpResponse(status=200, content_type="application/json", content=json.dumps(success))

#hopping concept
def payment_portal(request,*args,**kwargs):
    # if 'access_token' in request.session.keys():
    error = {}
    success = {}
    if "transaction_type" not in request.POST or "amount" not in request.POST or "event_id" not in request.POST:
        return HttpResponse("transaction_type not found")
    else:
        request.session["ACCESS_TOKEN"] = kwargs["access_token"]
        amount = request.POST["amount"]
        if request.POST["transaction_type"] == "EVENT":
            request.session["transaction_type"] = "EVENT"
            request.session["event_id"] = request.POST["event_id"]
        elif request.POST["transaction_type"]== "USER":
            request.session["transaction_type"] = "USER"
        else:
            error["details"] = "Unknown transaction type"
            return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))
    data_dict = {
        'MID': 'Rustic14665252659839',
        'ORDER_ID': 'RUSTIC'+str(random.randint(1, 100000)),
        'TXN_AMOUNT': amount,
        'CUST_ID': 'acfff@paytm.com',
        'INDUSTRY_TYPE_ID': 'Retail',
        'WEBSITE': 'WEB_STAGING',
        'CHANNEL_ID': 'WEB',
        'CALLBACK_URL': 'http://35.162.117.56:9090/process_payment/',
    }

    param_dict = data_dict
    param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(data_dict, MERCHANT_KEY)

    # for key in param_dict:
    #   print key.strip()+param_dict[key].strip()
    response = """
    <h1>Merchant Check Out Page</h1></br>
    <form method="post" action="https://pguat.paytm.com/oltp-web/processTransaction" name="f1">
    <table border="1">
    <tbody>"""
    for key in param_dict:
        response += '<input type="hidden" name="' + key.strip() + '"value="' + param_dict[key].strip() + '">'
    response += """"</tbody>
    </table>
    <script type="text/javascript">
    document.f1.submit();
    </script>
    </form>
    """

    return HttpResponse(response)
    # else:
    #     return HttpResponse("Error")

@csrf_exempt
def process_payment(request):
    global exitFlag
    exitFlag = 0
    checksum = None
    message = {}
    if request.method == "POST":
        respons_dict = {}

        for i in request.POST.keys():
            print i
            respons_dict[i] = request.POST[i]
            if i == 'CHECKSUMHASH':
                checksum = request.POST[i]

        if 'GATEWAYNAME' in respons_dict:
            if respons_dict['GATEWAYNAME'] == 'WALLET':
                respons_dict['BANKNAME'] = 'null'

        verify = Checksum.verify_checksum(respons_dict, MERCHANT_KEY, checksum)
        print verify

        if verify:
            if respons_dict['RESPCODE'] == '01':
                print "order successful"
                for element in ["SUBS_ID","PROMO_CAMP_ID","PROMO_STATUS","PROMO_RESPCODE"]:
                    if element not in respons_dict:
                        respons_dict[element] = None
                user_profile = UserProfileView.get_profile(request.session["ACCESS_TOKEN"])
                if request.session["transaction_type"] == "USER":
                    wallet = Wallet.objects.get(associated_user=user_profile.user)
                else:
                    event = Event.objects.get(pk=request.session["event_id"])
                    wallet = Wallet.objects.get(associated_event=event)
                with transaction.atomic():
                    amount = moneyed.Money(float(respons_dict['TXNAMOUNT']),respons_dict['CURRENCY'])
                    wallet.balance = wallet.balance+amount
                    wallet.save()
                    if request.session["transaction_type"] == "USER":
                        transaction_object = Transaction.objects.create(from_wallet=None,
                                                                       to_wallet=Wallet.objects.get(associated_user=user_profile.user),
                                                                       type='CREDIT',
                                                                       amount=amount, default_currency=respons_dict['CURRENCY'],
                                                                       status=respons_dict["STATUS"],
                                                                       order_id=respons_dict["ORDERID"],
                                                                       external_transaction_flag=True,
                                                                       external_subscription_id=respons_dict["SUBS_ID"],
                                                                       external_transaction_id=respons_dict["TXNID"],
                                                                       bank_transaction_id=respons_dict["BANKTXNID"],
                                                                       transaction_date=respons_dict["TXNDATE"],
                                                                       gateway_name=respons_dict["GATEWAYNAME"],
                                                                       bank_name=respons_dict["BANKNAME"],
                                                                       payment_mode=respons_dict["PAYMENTMODE"],
                                                                       promo_camp_id=respons_dict["PROMO_CAMP_ID"],
                                                                       promo_status=respons_dict["PROMO_STATUS"],
                                                                       promo_response_code=respons_dict["PROMO_RESPCODE"]
                                                                       )
                    else:
                        transaction_object = Transaction.objects.create(from_wallet=None,
                                                                        to_wallet=Wallet.objects.get(
                                                                            associated_event=event),
                                                                        type='CREDIT',
                                                                        amount=amount,
                                                                        default_currency=respons_dict['CURRENCY'],
                                                                        status=respons_dict["STATUS"],
                                                                        order_id=respons_dict["ORDERID"],
                                                                        external_transaction_flag=True,
                                                                        external_subscription_id=respons_dict[
                                                                            "SUBS_ID"],
                                                                        external_transaction_id=respons_dict["TXNID"],
                                                                        bank_transaction_id=respons_dict["BANKTXNID"],
                                                                        transaction_date=respons_dict["TXNDATE"],
                                                                        gateway_name=respons_dict["GATEWAYNAME"],
                                                                        bank_name=respons_dict["BANKNAME"],
                                                                        payment_mode=respons_dict["PAYMENTMODE"],
                                                                        promo_camp_id=respons_dict["PROMO_CAMP_ID"],
                                                                        promo_status=respons_dict["PROMO_STATUS"],
                                                                        promo_response_code=respons_dict[
                                                                            "PROMO_RESPCODE"]
                                                                        )
                    transaction_object.save()
                    if request.session["transaction_type"] == "EVENT":
                        members = event.members.all()
                        admins = event.admin.all()
                        workQueue = Queue.Queue(10)
                        queueLock.acquire()
                        for member in members:
                            notification_message = "Your friend "+user_profile.first_name+" contributed "+str(amount.amount)+" to event "+event.name
                            notification = Notification.objects.create_notification(notification_message, member, None)
                            notification.save()
                            serializer = NotificationSerializer(notification)
                            workQueue.put({"data":serializer.data,"destination":'/topic/notifications_' + str(member.id)})
                        for admin in admins:
                            notification_message = "Your friend " + user_profile.first_name + " contributed " + str(
                                amount.amount) + " to event " + event.name
                            notification = Notification.objects.create_notification(notification_message, admin, None)
                            notification.save()
                            serializer = NotificationSerializer(notification)
                            workQueue.put(
                                {"data": serializer.data, "destination": '/topic/notifications_' + str(admin.id)})
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
            else:
                print "order unsuccessful because" + respons_dict['RESPMSG']
        else:
            print "order unsuccessful because" + respons_dict['RESPMSG']
        message["details"] = respons_dict['RESPMSG']
        return HttpResponse(status=200, content_type="application/json",content=json.dumps(message))

@csrf_exempt
def send_address_request_notification(request, *args, **kwargs):
    error = {}
    access_token = kwargs['access_token']
    if "to_user_id" not in request.POST:
        error["details"] = "invalid params"
        return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))

    request_to_user = BdayAppUser.objects.get(pk=request.POST["to_user_id"])
    user_profile = UserProfileView.get_profile(access_token)
    if request_to_user in user_profile.app_friends.all():
        notification_message = "Your friend "+user_profile.first_name+" has requested your address."
        notification = Notification.objects.create_notification(notification_message, request_to_user, None, event_for_user=user_profile.user)
        notification.save()
        requested_by = UserSerializer(user_profile.user)
        success = {"details":"Success","requested_by":requested_by.data}
        return HttpResponse(status=200, content_type="application/json", content=json.dumps(success))
    else:
        error["details"] = "Unauthorized"
        return HttpResponse(status=401, content_type="application/json", content=json.dumps(error))

@csrf_exempt
def process_address_request(access_token, request):
    error = {}
    if "to_user_id" not in request.GET:
        error["details"] = "invalid params"
        return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))
    request_to_user = BdayAppUser.objects.get(pk=request.GET["to_user_id"])
    user_profile = UserProfileView.get_profile(access_token)
    fields_list = ["street_address", "address_line_2", "city", "state", "pincode"]
    success_dict = {}
    for field in fields_list:
        attribute_value = getattr(user_profile, field)
        if attribute_value is not None:
            success_dict[field] = attribute_value
        else:
            success_dict[field] = "Not Found"
    if request_to_user in user_profile.app_friends.all():
        # notification_message = "Your friend "+user_profile.first_name+"'s address is "+user_profile.address
        # notification = Notification.objects.create_notification(notification_message, request_to_user, None, event_for_user=user_profile.user)
        # notification.save()
        success = {"details": "Success","contact_information": success_dict}
        return HttpResponse(status=200, content_type="application/json", content=json.dumps(success))
    else:
        error["details"] = "Unauthorized"
        return HttpResponse(status=401, content_type="application/json", content=json.dumps(error))


def get_giftstore_data(request):
    error = {}
    categories = Category.objects.all()
    output_json = []
    #data = serializers.serialize('json', categories)
    for category in categories:
        category_json = {"name":category.name,"logo":category.logo.name}
        sub_categories = SubCategory.objects.filter(category=category)
        category_json["sub_categories"] = []
        for sub_category in sub_categories:
            sub_category_json = {"name":sub_category.name,"logo":sub_category.logo.name}
            sub_category_json["giftstores"] = []
            criterion_1 = Q(subcategory=sub_category)
            criterion_2 = Q(category=category)
            giftstores = GiftStore.objects.filter(criterion_1 & criterion_2)
            for giftstore in giftstores:
                giftstore_json = {"name":giftstore.name,"link":giftstore.link,"affiliated_link":giftstore.affiliated_link,"logo":giftstore.logo}
                sub_category_json["giftstores"].append(giftstore_json)
            category_json["sub_categories"].append(sub_category_json)
        output_json.append(category_json)
    return HttpResponse(status=200, content_type="application/json", content=json.dumps(output_json))
    #print output_json
    #dprint(categories)