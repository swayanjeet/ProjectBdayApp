from BdayApp.serializers import UserProfile, UserProfileSerializer, BdayAppUser, BdayAppUsermanager,  Reminder, Wallet
from rest_framework import generics
from rest_framework import response
from rest_framework import mixins, status, exceptions
import facebook
import logging
import json
import datetime
import moneyed

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UserProfileView(generics.GenericAPIView, mixins.UpdateModelMixin,mixins.RetrieveModelMixin):

    model = UserProfile
    serializer_class = UserProfileSerializer

    @staticmethod
    def handle_error(e):
        content = dict()
        logger.error(e)
        raise exceptions.APIException(e)

    @staticmethod
    def get_profile(access_token):
        content = dict()
        try:
            graph = facebook.GraphAPI(access_token=access_token, version='2.8')
            profile_id = graph.get_object(id='me')['id']
            user_profile = UserProfile.objects.get(profile_id__exact=str(profile_id))
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
                    break
        except Exception as e:
            UserProfileView.handle_error(e)

    def get(self, request, access_token,*args, **kwargs):
        try:
            user_profile = UserProfileView.get_profile(access_token=access_token)
            serializer = UserProfileSerializer(user_profile)
            UserProfileView.sync_friends(user_profile)
            logger.info("Completing get method")
            request.session.clear()
            request.session['access_token'] = user_profile.access_token
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
            user = BdayAppUser.objects.create_user()
            minimum_balance = moneyed.Money(0, 'INR')
            maximum_balance = moneyed.Money(100000, 'INR')
            wallet = Wallet.objects.create_wallet(minimum_balance, maximum_balance, 'U', 'INR', user, None)
            user_profile = UserProfile.objects.create_user_profile(access_token, request.data['profile_type'], user)
            serializer = UserProfileSerializer(user_profile)
            return response.Response(serializer.data)
        except Exception as e:
            UserProfileView.handle_error(e)