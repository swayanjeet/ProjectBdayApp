from __future__ import unicode_literals
from django.db import models
import facebook
import logging
import datetime
import stomp
import json

import moneyed
from djmoney.models.fields import MoneyField            
from djmoney.models.managers import money_manager
# Create your models here.
logger = logging.getLogger(__name__)

STOMP_SERVER_URL = '35.162.74.72'
STOMP_PORT = 61613


class BdayAppUsermanager(models.Manager):

    def create_user(self,email_id=None):
        user = self.create(email_id=email_id,creation_date=datetime.datetime.now())
        return user


class BdayAppUser(models.Model):
    email_id = models.EmailField(null=True)
    creation_date = models.DateTimeField()
    objects = BdayAppUsermanager()

    class Meta:
        ordering = ['-creation_date']

    def update_email_id(self,email_id):
        self.email_id = email_id
        self.save()


class EventManager(models.Manager):

    def create_event(self,admin,name,start_date,end_date=None,picture=None,members=None,type='DEFAULT'):
        event = self.create(name=name,start_date=start_date,end_date=end_date,picture=picture,type=type,creation_date=datetime.datetime.now())
        logger.info(event.id)
        event.admin.add(admin)
        if members is not None:
            for member in members:
                event.members.add(member)
        event.save()
        UnreadChatBuffer.objects.create(event=event, user=admin, last_read_chat=None)
        return event


class Event(models.Model):
    # id = models.BigAutoField()
    picture = models.ImageField(upload_to='images/%Y/%m/%d', null=True)
    admin = models.ManyToManyField(BdayAppUser, related_name='admin',null=True,blank=True)
    members = models.ManyToManyField(BdayAppUser, related_name='members', null=True,blank=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100, default='DEFAULT')
    creation_date = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True,blank=True)

    objects = EventManager()

    class Meta:
        ordering = ['-creation_date', 'name']

    def __update_picture(self,picture):
        if picture is not None:
            self.picture = picture
            self.save()

    def __update_admins(self, users):
        if users is not None:
            for user in users:
                self.admin.add(user)
            self.save()
    def __remove_admin(self,users):
        if users is not None:
            for user in users:
                self.admin.add(user)
            self.save()
    # Users is a list
    def __update_members(self,users):
        if users is not None:
            for user in users:
                self.members.add(user)
            self.save()
    def __remove_members(self,users):
        if users is not None:
            for user in users:
                self.members.remove(user)
            self.save()
    def __update_name(self,name):
        if name is not None:
            self.name = name
            self.save()

    def __update_start_date(self,start_date):
        if start_date is not None:
            self.start_date = start_date
            self.save()

    def __update_end_date(self,end_date):
        if end_date is not None:
            self.end_date = end_date
            self.save()

    def __remove_picture(self):
        self.picture = None
        self.save()

    def update(self,picture=None,admins=None,members=None,name=None,start_date=None,end_date=None):
        self.__update_picture(picture)
        self.__update_admins(admins)
        self.__update_members(members)
        self.__update_name(name)
        self.__update_start_date(start_date)
        self.__update_end_date(end_date)


class ReminderManager(models.Manager):

    def create_reminder(self,name,date,user,event_associated_flag=False,associated_event=None,picture=None,type=None,reminder_for=None,picture_file=None):
        reminder = self.create(name=name,reminder_date=date,user=user,event_associated_flag=event_associated_flag,associated_event=associated_event,picture=picture,type=type,reminder_for=reminder_for,picture_file=picture_file,creation_date = datetime.datetime.now())
        return reminder


class Reminder(models.Model):
    picture = models.URLField(null=True,blank=True)
    picture_file = models.ImageField(upload_to='images/%Y/%m/%d', null=True)
    reminder_date = models.DateField()
    name = models.CharField(max_length=50)
    event_associated_flag = models.BooleanField(default=False)
    associated_event = models.OneToOneField(Event, default=None, null=True, blank=True)
    user = models.ForeignKey(BdayAppUser)
    creation_date = models.DateTimeField()
    type = models.CharField(max_length=50, default='CUSTOM')
    reminder_for = models.ForeignKey(BdayAppUser, default=None, null=True, blank=True,related_name='reminder_for')
    objects = ReminderManager()

    class Meta:
        ordering = ['-creation_date', 'name']

    def __update_picture(self,picture):
        if picture is not None:
            self.picture = picture
            self.save()

    def __update_reminder_date(self,date):
        if date is not None:
            self.reminder_date = date
            self.save()

    def __update_name(self,name):
        if name is not None:
            self.name = name
            self.save()

    def __update_event_associated_flag(self,flag):
        if flag is not None:
            self.event_associated_flag = flag
            self.save()

    def __update_associated_event(self,event):
        if event is not None:
            self.associated_event = event
            self.save()

    def update_reminder(self,picture=None,date=None,name=None,event_associated_flag=None,associated_event=None):
        self.__update_picture(picture)
        self.__update_reminder_date(date)
        self.__update_name(name)
        self.__update_event_associated_flag(event_associated_flag)
        self.__update_associated_event(associated_event)


class UserProfileManager(models.Manager):

    def create_user_profile(self,access_token,profile_type,user):
        try:
            birthday, profile_id, user_name, picture, first_name, last_name, gender = None, None,None,None, None, None, None
            #total_number_of_friends_on_app = 0
            if profile_type == "FB":
                graph = facebook.GraphAPI(access_token=access_token, version='2.8')
                profile_id = graph.get_object(id='me')['id']
                #user_name = graph.get_object(id='me')['name']
                picture = graph.get_object(id='me', fields='picture')['picture']['data']['url']
                response_string_ = graph.get_object(id='me',fields = 'birthday,email,first_name,last_name,gender,name')
                if 'birthday' in response_string_:
                    birthday = response_string_['birthday']
                if 'email' in response_string_:
                    if user.email_id is None:
                        user.email_id = response_string_['email']
                        user.save()
                if 'name' in response_string_:
                    user_name = response_string_['name']

                if 'first_name' in response_string_:
                    first_name = response_string_['first_name']

                if 'last_name' in response_string_:
                    last_name = response_string_['last_name']

                if 'gender' in response_string_:
                    gender = response_string_['gender']

                user_profile = self.create(access_token=access_token,profile_id=profile_id,birthday=birthday,picture=picture,profile_type=profile_type,user=user,user_name=user_name,first_name=first_name,last_name=last_name,gender=gender,creation_date = datetime.datetime.now(),phone_number=None)
                user_profile.save()
                friends = graph.get_connections('me', "friends")
                while True:
                    try:
                        for friend in friends['data']:
                            id = friend['id'].encode('utf-8')
                            try:
                                if UserProfile.objects.get(profile_id=id) is not None:
                                    friends_profile = UserProfile.objects.get(profile_id=id)
                                    user_profile.app_friends.add(friends_profile.user)
                                    friends_profile.app_friends.add(user)
                                    if friends_profile.birthday is not None:
                                        friends_bday_reminder = Reminder.objects.create_reminder(friends_profile.user_name+"'s Bday",
                                                                         datetime.datetime.strptime(
                                                                            friends_profile.birthday, '%m/%d/%Y'),
                                                                         user_profile.user, False, None, friends_profile.picture,
                                                                         type='FACEBOOK',
                                                                         reminder_for=friends_profile.user
                                                                         )
                                        friends_bday_reminder.save()
                                    if user_profile.birthday is not None:
                                        self_bday_reminder_for_friends = Reminder.objects.create_reminder(user_profile.user_name+"'s Bday",
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
                        friends = graph.get_connections("me", "friends", after=friends['paging']['cursors']['after'])
                    except KeyError:
                        # When there are no more pages (['paging']['next']), break from the
                        # loop and end the script.
                        break
                logger.debug("facebook type user profile created successfully")
                user_profile.save()
                return user_profile
        except Exception as e:
            logger.error(e)
            logger.error("could not create user profile")


class UserProfile(models.Model):
    # id = models.BigAutoField()
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    phone_number = models.DecimalField(max_digits=10, null=True, decimal_places=0)
    gender = models.CharField(max_length=15, null=True)
    user_name = models.CharField(max_length=50)
    profile_id = models.CharField(max_length=50, unique=True)
    picture = models.URLField()
    access_token = models.CharField(max_length=150)
    user = models.OneToOneField(BdayAppUser, null=True, blank=True, related_name='user_id')
    app_friends = models.ManyToManyField(BdayAppUser, null=True, symmetrical=True, related_name='friends')
    profile_type = models.CharField(max_length=2, choices=(
        ('FB', 'FACEBOOK'),
        ('GP', 'GOOGLEPLUS')
    ))
    birthday = models.CharField(max_length=10,null=True,blank=True)
    street_address = models.CharField(max_length=10, null=True, blank=True)
    address_line_2 = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=10, null=True, blank=True)
    state = models.CharField(max_length=10, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    #address = models.CharField(max_length=100,null=True,blank=True)
    contact_privacy_field = models.CharField(max_length=10, choices=(
        ('PUBLIC', 'PB'),
        ('PRIVATE', 'PV')
    ), default='PV')
    creation_date = models.DateTimeField()
    objects = UserProfileManager()
    class Meta:
        ordering = ['-creation_date']

    def __get_user_name(self):
        try:
            if self.profile_type is "FB":
                graph = facebook.GraphAPI(access_token=self.access_token, version='2.8')
                self.user_name = graph.get_object(id='me')['name']
            logger.info("user_name stored successfully")
        except Exception as e:
            logger.error(e)
    def __get_profile_id(self):
        try:
            if self.profile_type is "FB":
                graph = facebook.GraphAPI(access_token=self.access_token, version='2.8')
                self.profile_id = graph.get_object(id='me')['id']
            logger.info("profile_id stored successfully")
        except Exception as e:
            logger.error(e)
    def __get_picture(self):
        try:
            if self.profile_type is "FB":
                graph = facebook.GraphAPI(access_token=self.access_token, version='2.8')
                self.picture = graph.get_object(id='me', fields='picture')['picture']['data']['url']
            logger.info("profile picture updated successfully")
        except Exception as e:
            logger.error(e)
    def __get_birthday(self):
        try:
            if self.profile_type is "FB":
                graph = facebook.GraphAPI(access_token=self.access_token, version='2.8')
                response_string_ = graph.get_object(id='me', fields='birthday')
                if 'birthday' in response_string_:
                    self.birthday = response_string_['birthday']
                    logger.info("birthday is " +self.birthday)
            logger.info("birthday stored successfully")
        except Exception as e:
            logger.error(e)
    def __get_email(self):
        try:
            if self.profile_type is "FB":
                graph = facebook.GraphAPI(access_token=self.access_token, version='2.8')
                response_string_ = graph.get_object(id='me', fields='email')
                if 'email' in response_string_:
                    logger.info("email is : " + response_string_['email'])
                    return response_string_['email']
            logger.info("email_id stored successfully")
        except Exception as e:
            logger.error(e)
    def __get_friends(self):
        friends_list = []
        try:
            if self.profile_type is "FB":
                graph = facebook.GraphAPI(access_token=self.access_token, version='2.8')
                friends = graph.get_connections('me', "friends")
                while True:
                    try:
                        for friend in friends['data']:
                            id = friend['id'].encode('utf-8')
                            friends_list.append(id)
                        # Attempt to make a request to the next page of data, if it exists.
                        friends = graph.get_connections("me", "friends", after=friends['paging']['cursors']['after'])
                    except KeyError:
                        # When there are no more pages (['paging']['next']), break from the
                        # loop and end the script.
                        break
                return friends_list
        except Exception as e:
            logger.error(e)
            return friends_list
    def update_user_name(self,user_name):
        try:
            if user_name is not None:
                self.user_name = user_name
                self.save()
                logger.info("user_name updated")
        except Exception as e:
            logger.error(e)
    def update_picture(self,picture):
        try:
            if picture is not None:
                self.picture = picture
                self.save()
                logger.info("picture updated successfully")
        except Exception as e:
            logger.error(e)
    def update_access_token(self,access_token):
        try:
            if self.access_token is not None:
                self.access_token = access_token
                logger.info("access_token updated successfully")
        except Exception as e:
            logger.error(e)
    def update_picture_from_social_network(self):
        try:
            if self.profile_type is "FB":
                self.__get_picture()
                self.save()
                logger.info("picture updated from social network")
        except Exception as e:
            logger.error(e)
    def update_app_friends(self):
        try:
            users = self.__get_friends()
            if users is not None:
                for profile_id in users:
                    try:
                        if UserProfile.objects.get(profile_id=profile_id) is not None:
                            friends_profile = UserProfile.objects.get(profile_id=profile_id)
                            self.app_friends.add(friends_profile.user)
                            if friends_profile.birthday is not None:
                                friends_bday_reminder = Reminder.objects.create_reminder(friends_profile.user_name,
                                                                                         datetime.datetime.strptime(
                                                                                             friends_profile.birthday,
                                                                                             '%m/%d/%Y'),
                                                                                         self.user, False, None,
                                                                                         friends_profile.picture
                                                                                         )
                                friends_bday_reminder.save()
                            if self.birthday is not None:
                                self_bday_reminder_for_friends = Reminder.objects.create_reminder(self.user_name,
                                                                                         datetime.datetime.strptime(
                                                                                             self.birthday,
                                                                                             '%m/%d/%Y'),
                                                                                         friends_profile.user, False, None,
                                                                                         self.picture
                                                                                         )
                                self_bday_reminder_for_friends.save()
                    except UserProfile.DoesNotExist:
                        continue
            self.save()
            logger.info("friend list updated successfully")
        except Exception as e:
            logger.error(e)


class MessageManager(models.Manager):
    def create_message(self,message,to_,from_,is_read=False,read_date=None):
        message = self.create(message=message,to_field=to_,from_field=from_,creation_date=datetime.datetime.now(),is_read=False,read_date=None)
        return message


class Message(models.Model):
    message = models.CharField(max_length=1000)
    to_field = models.ForeignKey(BdayAppUser, related_name='to_')
    from_field = models.ForeignKey(BdayAppUser, related_name='from_')
    creation_date = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    read_date = models.DateTimeField(null=True,blank=True)
    objects = MessageManager()

    class Meta:
        ordering = ['-creation_date']


class NotificationManager(models.Manager):
    def create_notification(self,message,associated_user,url,is_read=False,read_date=None,type=None,event_reminder_type=None,event_for_user=None,event=None):
        notification = self.create(message=message,associated_user=associated_user,creation_date=datetime.datetime.now(),url=url,is_read=False,type=type,event_reminder_type=event_reminder_type,event_for_user=event_for_user,event=event)
        return notification


class Notification(models.Model):
    message = models.CharField(max_length=1000)
    associated_user = models.ForeignKey(BdayAppUser)
    type = models.CharField(max_length=500,null=True,blank=True)
    event_reminder_type = models.CharField(max_length=500,null=True,blank=True)
    event_for_user = models.ForeignKey(BdayAppUser, related_name='event_for_user', null=True, blank=True)
    event = models.ForeignKey(Event, null=True, blank=True)
    creation_date = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    url = models.URLField(null=True,blank=True)
    read_date = models.DateTimeField(null=True, blank=True)
    objects = NotificationManager()
    class Meta:
        ordering = ['-creation_date']

class WishManager(models.Manager):
    def create_wish(self,url,name,website_name,website_url,price,picture,user=None,event=None):
        wish = self.create(url=url,name=name,website_name=website_name,website_url=website_url,
                           price=price,picture=picture,user=user,event=event,creation_date=datetime.datetime.now())
        return wish


class Wish(models.Model):
    url = models.URLField()
    name = models.CharField(max_length=500)
    website_name = models.CharField(max_length=500)
    website_url = models.URLField()
    price = models.FloatField()
    picture = models.URLField()
    creation_date = models.DateTimeField()
    user = models.ForeignKey(BdayAppUser,null=True)
    event = models.ForeignKey(Event, null=True)
    objects = WishManager()
    class Meta:
        ordering = ['-creation_date']

class ChatManager(models.Manager):
    def create_event_chat(self, event, user,wish = None,message_field=None, url_field=None, file_field = None, type='LR',creation_date = datetime.datetime.now()):
        if message_field is None and url_field is None and file_field is None:
            pass
        else:
            event_chat = self.create(event=event,wish = wish,message_field = message_field, url_field = url_field, file_field = file_field, user=user,type=type,creation_date = creation_date)
            return event_chat

class EventChat(models.Model):
    event = models.ForeignKey(Event)
    message_field = models.CharField(max_length=100,null=True)
    creation_date = models.DateTimeField()
    type = models.CharField(max_length=100)
    url_field = models.URLField(null=True)
    file_field = models.ImageField(upload_to='images/%Y/%m/%d', null=True)
    wish = models.ForeignKey(Wish,null=True)
    user = models.ForeignKey(BdayAppUser)
    objects = ChatManager()

    class Meta:
        ordering = ['-id']

class WalletManager(models.Manager):
    def create_wallet(self, minimum_balance, maximum_balance, type, default_currency, associated_user, associated_event, creation_date=datetime.datetime.now()):
        initial_balance = moneyed.Money(0, 'INR')
        wallet = self.create(balance=initial_balance,minimum_balance=minimum_balance, maximum_balance=maximum_balance,type=type,default_currency=default_currency,associated_user=associated_user,associated_event=associated_event, creation_date=creation_date)
        return wallet

class Wallet(models.Model):
    balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
    minimum_balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
    maximum_balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
    type = models.CharField(max_length=20, choices=(
        ('U','USER'),
        ('E','EVENT')
    ))
    default_currency = models.CharField(max_length=20)
    associated_user = models.OneToOneField(BdayAppUser, related_name='user_wallet', null=True)
    associated_event = models.OneToOneField(Event, related_name='event_wallet', null=True)
    creation_date = models.DateTimeField()
    objects = money_manager(WalletManager())

# class GroupieWallet(models.Model):
#     balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
#     minimum_balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
#     maximum_balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
#     type = models.CharField(max_length=20, choices=(
#         ('U','USER'),
#         ('E','EVENT')
#     ))
#     default_currency = models.CharField(max_length=20)
#     associated_user = models.OneToOneField(BdayAppUser, related_name='user_wallet', null=True)
#     associated_event = models.OneToOneField(Event, related_name='event_wallet', null=True)
#     creation_date = models.DateTimeField()
#     objects = money_manager(WalletManager())


class Transaction(models.Model):
    from_wallet = models.ForeignKey(Wallet, related_name='from_wallet', null=True)
    to_wallet = models.ForeignKey(Wallet, related_name='to_wallet', null=True)
    type = models.CharField(max_length=20, choices=(
        ('D','DEBIT'),
        ('C','CREDIT')
    ))
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
    default_currency = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=(
        ('S', 'TXN_SUCCESS'),
        ('P', 'PENDING'),
        ('F', 'TXN_FAILURE'),
        ('O', 'OPEN')
    ))
    order_id = models.CharField(max_length=1000, null=True)
    external_transaction_flag = models.BooleanField()
    external_subscription_id = models.BigIntegerField(null=True)
    external_transaction_id = models.BigIntegerField(null=True)
    bank_transaction_id = models.CharField(max_length=100,null=True)
    # external_response_code = models.CharField(max_length=100, null=True)
    # external_response_message = models.CharField(max_length=100, null=True)
    transaction_date = models.DateTimeField()
    gateway_name = models.CharField(max_length=100, null=True)
    bank_name = models.CharField(max_length=100, null=True)
    payment_mode = models.CharField(max_length=100, null=True)
    promo_camp_id = models.CharField(max_length=100, null=True)
    promo_status = models.CharField(max_length=100, null=True)
    promo_response_code = models.CharField(max_length=100, null=True)
    #checksum_hash = models.CharField(max_length=1000, null=True)
    objects = money_manager(models.Manager())

class UnreadChatBuffer(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(BdayAppUser)
    last_read_chat = models.ForeignKey(EventChat,null=True,blank=True)

class Category(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='images/%Y/%m/%d')

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='images/%Y/%m/%d')
    category = models.ForeignKey(Category)

class GiftStore(models.Model):
    name = models.CharField(max_length=100)
    link = models.URLField()
    affiliated_link = models.URLField()
    logo = models.URLField()
    category = models.ForeignKey(Category)
    subcategory = models.ForeignKey(SubCategory)

class OtherLifeEvents(models.Model):
    name = models.CharField(max_length=100)
    date_of_event = models.DateTimeField()
    created_date = models.DateTimeField(default=datetime.datetime.now)
    type = models.CharField(max_length=100, default='DEFAULT')
    user = models.ForeignKey(BdayAppUser, related_name='other_life_events', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_date']


class CashoutCard(models.Model):
    type = models.CharField(max_length=100)
    terms_and_conditions = models.CharField(max_length=3000, null=True, blank=True)
    shipping_and_handling = models.CharField(max_length=3000, null=True, blank=True)
    brand_details = models.CharField(max_length=1000, null=True, blank=True)
    coupon_code = models.CharField(max_length=100)
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
    user = models.ForeignKey(BdayAppUser, related_name='cards', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=datetime.datetime.now)
    cashout_transaction_id = models.ForeignKey(Transaction, null=True, blank=True)
    associated_event = models.ForeignKey(Event, null=True, blank=True, related_name="associated_event")
    objects = money_manager(models.Manager())

class CashoutMessage(models.Model):
    text = models.CharField(max_length=400)
    user = models.ForeignKey(BdayAppUser, on_delete=models.CASCADE)
    associated_event = models.ForeignKey(Event, null=True, blank=True, related_name="associated_event")

class GroupyWallet(models.Model):
    balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
    minimum_balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
    maximum_balance = MoneyField(max_digits=10, decimal_places=2, default_currency='INR')
    default_currency = models.CharField(max_length=20)
    associated_user = models.OneToOneField(BdayAppUser, related_name='user_wallet', null=True)
    creation_date = models.DateTimeField()
    objects = money_manager(models.Manager())
    deduct_percentage = models.DecimalField(max_digits=2)

