from django.http import HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import logging
from BdayApp.print_queryset import dprint
from BdayApp.models import BdayAppUser, BdayAppUsermanager, UserProfile, UserProfileManager, Wallet, Transaction, Event, Notification, EventChat
from BdayApp.UserProfileView import UserProfileView
from BdayApp.constants import notification_types, DAYS_OF_THE_YEAR
import datetime
import json
import facebook
import Checksum
import moneyed
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Create your views here.
MERCHANT_KEY = 'fs6lxL&StfY4ZTwL'
ACCESS_TOKEN = "EAAX7retDkCcBAGslxPY8WMIKYe2mMuQdZCJgcafKQfWx7AXqr7nmXyGF60LOHtwzE7i7e0ZCyIEJQoe17VuKOI46T4DYKbIT9ZC7K4kxibuSAOBn3FyLmauOu1Pwivp3W3JkdOTKHJK1s0ulqrAGZCiuiD5ZAACCbqPtQ8AwjoSI0o60sAnhTdfAzEPN7u9msJydD6ZB0D4N5NsDfUJTJZCtkZAb1Lz3BLcZD"
EVENT_ID = '38'

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
        #dprint(UserProfile.objects.get(user=profile.user))
        message = "Team Bdayapp wishes you a very happy birthday"
        url = None
        user = profile.user
        notification = Notification.objects.create_notification(message, user, url, type=notification_types["NONE"])
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
            message = "Your friend "+profile.first_name+" has birthday on "+added_date_time.strftime("%d %b")
            print message
            url = None
            user = friend
            type = "FRIENDS_EVENT_REMINDER"
            event_reminder_type = "BIRTHDAY"
            event_for_user = profile.user
            notification = Notification.objects.create_notification(message, user, url, type=type, event_reminder_type=event_reminder_type, event_for_user=event_for_user)
            notification.save()
    success["details"] = "success"
    return HttpResponse(status=200, content_type="application/json", content=json.dumps(success))

#hopping concept
def payment_portal(request):
    # if 'access_token' in request.session.keys():
    error = {}
    success = {}
    if "transaction_type" not in request.GET:
        return HttpResponse("transaction_type not found")
    else:
        if request.GET["transaction_type"] == "EVENT":
            request.session["transaction_type"] = "EVENT"
        elif request.GET["transaction_type"]== "USER":
            request.session["transaction_type"] = "USER"
        else:
            error["details"] = "Unknown transaction type"
            return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))
    data_dict = {
        'MID': 'Rustic14665252659839',
        'ORDER_ID': 'RUSTIC'+str(random.randint(1, 100000)),
        'TXN_AMOUNT': '1',
        'CUST_ID': 'acfff@paytm.com',
        'INDUSTRY_TYPE_ID': 'Retail',
        'WEBSITE': 'WEB_STAGING',
        'CHANNEL_ID': 'WEB',
        'CALLBACK_URL':'http://localhost:3000/process_payment/',
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
                user_profile = UserProfileView.get_profile(ACCESS_TOKEN)
                if request.session["transaction_type"] == "USER":
                    wallet = Wallet.objects.get(associated_user=user_profile.user)
                else:
                    event = Event.objects.get(pk=EVENT_ID)
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
                        chat = EventChat.objects.create_event_chat(Event.objects.get(pk=event.id), user_profile.user, wish=None,
                                                                   message_field=user_profile.user.id+" contributed "+str(amount.amount),
                                                                   url_field=None,
                                                                   file_field=None, type='CENTER')
                        chat.save()
                        members = event.members
                        for member in members:
                            notification_message = "Your friend "+user_profile.first_name+" contributed "+str(amount.amount)+" to event "+event.name
                            notification = Notification.objects.create_notification(notification_message, member, None)
                            notification.save()
            else:
                print "order unsuccessful because" + respons_dict['RESPMSG']
        else:
            print "order unsuccessful because" + respons_dict['RESPMSG']
        message["details"] = respons_dict['RESPMSG']
        return HttpResponse(status=200, content_type="application/json",content=json.dumps(message))


def send_address_request_notification(access_token, request):
    error = {}
    if "to_user_id" not in request.GET:
        error["details"] = "invalid params"
        return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))

    request_to_user = BdayAppUser.objects.get(pk=request.GET["to_user_id"])
    user_profile = UserProfileView.get_profile(access_token)
    if request_to_user in user_profile.app_friends.all():
        notification_message = "Your friend "+user_profile.first_name+" has requested your address."
        notification = Notification.objects.create_notification(notification_message, request_to_user, None, event_for_user=user_profile.user)
        notification.save()
        success = {"details":"Success"}
        return HttpResponse(status=200, content_type="application/json", content=json.dumps(success))
    else:
        error["details"] = "Unauthorized"
        return HttpResponse(status=401, content_type="application/json", content=json.dumps(error))


def process_address_request(access_token, request):
    error = {}
    if "to_user_id" not in request.GET:
        error["details"] = "invalid params"
        return HttpResponse(status=500, content_type="application/json", content=json.dumps(error))
    request_to_user = BdayAppUser.objects.get(pk=request.GET["to_user_id"])
    user_profile = UserProfileView.get_profile(access_token)
    if user_profile.address is None:
        error["details"] = "Address not found"
        return HttpResponse(status=404, content_type="application/json",  content=json.dumps(error))
    if request_to_user in user_profile.app_friends.all():
        notification_message = "Your friend "+user_profile.first_name+"'s address is "+user_profile.address
        notification = Notification.objects.create_notification(notification_message, request_to_user, None, event_for_user=user_profile.user)
        notification.save()
        success = {"details": "Success"}
        return HttpResponse(status=200, content_type="application/json", content=json.dumps(success))
    else:
        error["details"] = "Unauthorized"
        return HttpResponse(status=401, content_type="application/json", content=json.dumps(error))
