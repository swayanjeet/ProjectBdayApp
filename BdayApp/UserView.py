from BdayApp.serializers import UserSerializer, BdayAppUser, BdayAppUsermanager, Wallet
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions
from BdayApp.UserProfileView import UserProfileView
import moneyed 
import logging
import traceback

logger = logging.getLogger(__name__)

class UserView(generics.CreateAPIView,generics.RetrieveUpdateAPIView):

    model = BdayAppUser
    serializer_class = UserSerializer

    @staticmethod
    def handle_error(e):
        logger.error(e)
        logger.error(traceback.format_exc())
        raise exceptions.APIException(e)

    def get(self, request, *args, **kwargs):
        try:
            access_token = kwargs['access_token']
            user = BdayAppUser.objects.select_related('user_id').select_related('user_wallet').get(id=UserProfileView.get_profile(access_token).user.id)
            serializer = UserSerializer(user)
            return response.Response(serializer.data)
        except Exception as e:
            UserView.handle_error(e)

    def put(self, request, *args, **kwargs):
        try:
            access_token = kwargs['access_token']
            user = UserProfileView.get_profile(access_token).user
            serializer = UserSerializer(user, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return response.Response(serializer.data)
        except Exception as e:
            UserView.handle_error(e)

    def post(self, request, *args, **kwargs):
        try:
            user = BdayAppUser.objects.create_user(email_id=request.data['email_id'])
            minimum_balance  = moneyed.Money(0, 'INR')
            maximum_balance = moneyed.Money(100000, 'INR')
            wallet = Wallet.objects.create_wallet(minimum_balance, maximum_balance, 'U', 'INR', user, None)
            serializer = UserSerializer(user)
            return response.Response(serializer.data)
        except Exception as e:
            UserView.handle_error(e)