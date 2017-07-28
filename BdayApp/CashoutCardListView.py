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


class CashoutCardListView(generics.ListAPIView):

    model = CashoutCard
    parser_classes = (parsers.JSONParser,parsers.MultiPartParser,parsers.FormParser,)
    serializer_class = CashOutCardSerializer

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get_queryset(self):
        try:
            logger.info("Starting function get_queryset")
            access_token = self.kwargs['access_token']
            logger.info("access token is "+access_token)
            user = UserProfile.objects.get(profile_id__exact='1069321953161548').user#UserProfileView.get_profile(access_token).user
            logger.info("user found from access token")
            cash_out_card_list = CashoutCard.objects.filter(user=user)
            logger.info("other life events list found")
            logger.info("Completing function get_queryset")
            return cash_out_card_list
        except CashoutCard.DoesNotExist:
            raise exceptions.NotFound("event not found")
        except Exception as e:
            CashoutCardListView.handle_error(e)