import logging
import traceback
import datetime
import moneyed

from rest_framework import generics
from rest_framework import response
from rest_framework import status
from rest_framework import exceptions, filters
from rest_framework import parsers

from BdayApp.serializers import CashOutCardSerializer
from BdayApp.models import BdayAppUser, UserProfile, CashoutCard, Transaction, Event
from BdayApp.UserProfileView import UserProfileView

logger = logging.getLogger(__name__)

GIFT_CARD_API_URL = "sandbox.giftcardsindia.in"
GIFT_CARD_SECRET_ID = "66f634195b08f1debf2fce3f568121a6"
GIFT_CARD_SECRET_KEY = "ce31d33e9e69417f208f4895b5c051c0e862706bc2a006413af5db754008c466"

class CashoutCardView(generics.CreateAPIView, generics.RetrieveUpdateDestroyAPIView):

    model = CashoutCard
    parser_classes = (parsers.JSONParser,parsers.MultiPartParser,parsers.FormParser,)
    serializer_class = CashOutCardSerializer

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def create_gift_card(self):
        pass

    def put(self, request, *args, **kwargs):
        to_user_id = None
        card_id = None
        try:
            logger.info("Starting function PUT")
            access_token = self.kwargs['access_token']
            logger.info("access token is " + access_token)
            user = UserProfile.objects.get(
                profile_id__exact='1069321953161548').user  # UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")
            if "to_user_id" not in request.data or "card_id" not in request.data:
                raise exceptions.APIException("to_user_id/card_id not provided")
            to_user_id = request.data['to_user_id']
            card_id = request.data['card_id']
            card = CashoutCard.objects.get(pk=int(card_id))
            if user not in card.associated_event.admin.all():
                raise exceptions.PermissionDenied()
            to_user = BdayAppUser.objects.get(pk=int(to_user_id))
            card.user = to_user
            card.save()
        except BdayAppUser.DoesNotExist:
            raise exceptions.NotFound("to_user_id "+to_user_id+" not found")
        except CashoutCard.DoesNotExist:
            raise exceptions.NotFound("card with card id "+card_id+" not found")
        except Exception as error:
            CashoutCardView.handle_error(error)

    def post(self, request, *args, **kwargs):
        try:
            logger.info("Starting function POST")
            access_token = self.kwargs['access_token']
            logger.info("access token is "+access_token)
            user = UserProfile.objects.get(profile_id__exact='1069321953161548').user#UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")

            if "amount" not in request.data or "type" not in request.data or "event_id" not in request.data:
                raise exceptions.APIException("amount/type/event_id not provided")

            if request.data["type"] is "GIFT_CARD":
                if "brand_name" not in request.data:
                    raise exceptions.APIException("brand_name not provided")

            event = Event.objects.get(pk=int(request.data['event_id']))
            if user not in event.admin.all():
                raise exceptions.APIException()
            amount = moneyed.Money(float(request.data['amount']), 'INR')
            type = request.data["type"]
            terms_and_conditions = "Hello Terms and Conditions"
            shipping_and_handling = "Shipping and Handling"
            brand_details = "demo brand details"
            coupon_code = "ARIG1234"

            new_card = CashoutCard.objects.create(type=type, amount=amount, terms_and_conditions=terms_and_conditions, shipping_and_handling=shipping_and_handling, brand_details=brand_details, associated_event=event,coupon_code=coupon_code)
            new_card.save()
            cashout_transaction = Transaction.objects.create(from_wallet=event.event_wallet, to_wallet=None, type='D', amount=amount, default_currency="INR", status="S", transaction_date = datetime.datetime.now())
            cashout_transaction.save()

            new_card_serializer = CashOutCardSerializer(new_card)
            logger.info("other life events list found")
            logger.info("Completing function POST")
            return response.Response(new_card_serializer.data)
        except Event.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except Exception as e:
            CashoutCardView.handle_error(e)