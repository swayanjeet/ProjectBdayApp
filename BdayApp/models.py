from __future__ import unicode_literals

from django.db import models
import facebook
import logging
import datetime
# Create your models here.
logger = logging.getLogger(__name__)


class BdayAppUsermanager(models.Manager):

    def create_user(self,email_id=None):
        logger.info(email_id)
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

    def create_event(self,admin,name,start_date,end_date,picture=None,members=None):
        event = self.create(name=name,start_date=start_date,end_date=end_date,picture=picture,creation_date=datetime.datetime.now())
        logger.info(event.id)
        event.admin.add(admin)
        if members is not None:
            for member in members:
                event.members.add(member)
        event.save()
        return event


class Event(models.Model):
    # id = models.BigAutoField()
    picture = models.URLField(null=True)
    admin = models.ManyToManyField(BdayAppUser, related_name='admin',null=True,blank=True)
    members = models.ManyToManyField(BdayAppUser, related_name='members',null=True,blank=True)
    name = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

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

    def create_reminder(self,name,date,user,event_associated_flag=False,associated_event=None,picture=None):
        reminder = self.create(name=name,reminder_date=date,user=user,event_associated_flag=event_associated_flag,associated_event=associated_event,picture=picture,creation_date = datetime.datetime.now())
        return reminder

class Reminder(models.Model):
    picture = models.URLField(null=True)
    reminder_date = models.DateField()
    name = models.CharField(max_length=50)
    event_associated_flag = models.BooleanField(default=False)
    associated_event = models.OneToOneField(Event, default=None, null=True, blank=True)
    user = models.ForeignKey(BdayAppUser)
    creation_date = models.DateTimeField()
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
            birthday, profile_id, user_name, picture = None, None,None,None
            if profile_type == "FB":
                graph = facebook.GraphAPI(access_token=access_token, version='2.8')
                profile_id = graph.get_object(id='me')['id']
                user_name = graph.get_object(id='me')['name']
                picture = graph.get_object(id='me', fields='picture')['picture']['data']['url']
                response_string_ = graph.get_object(id='me',fields='birthday,email')
                if 'birthday' in response_string_:
                    birthday = response_string_['birthday']
                if 'email' in response_string_:
                    if user.email_id is None:
                        user.update_email_id(response_string_['email'])

                user_profile = self.create(access_token=access_token,profile_id=profile_id,birthday=birthday,picture=picture,profile_type=profile_type,user=user,user_name=user_name,creation_date = datetime.datetime.now())
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
                                                                         user_profile.user, False, None, friends_profile.picture
                                                                         )
                                        friends_bday_reminder.save()
                                    if user_profile.birthday is not None:
                                        self_bday_reminder_for_friends = Reminder.objects.create_reminder(user_profile.user_name+"'s Bday",
                                                                                                          datetime.datetime.strptime(
                                                                                                              user_profile.birthday,
                                                                                                              '%m/%d/%Y'),
                                                                                                          friends_profile.user,
                                                                                                          False, None,
                                                                                                          user_profile.picture
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
    address = models.CharField(max_length=100,null=True,blank=True)
    address_privacy_field = models.CharField(max_length=10, choices=(
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
    def create_notification(self,message,associated_user,url,is_read=False,read_date=None):
        notification = self.create(message=message,associated_user=associated_user,creation_date=datetime.datetime.now(),url=url,is_read=False)
        return notification


class Notification(models.Model):
    message = models.CharField(max_length=1000)
    associated_user = models.ForeignKey(BdayAppUser)
    creation_date = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    url = models.URLField(null=True,blank=True)
    read_date = models.DateTimeField(null=True, blank=True)
    objects = NotificationManager()
    class Meta:
        ordering = ['-creation_date']



class WishManager(models.Manager):
    def create_wish(self,url,name,website_name,website_url,price,picture,user):
        wish = self.create(url=url,name=name,website_name=website_name,website_url=website_url,
                           price=price,picture=picture,user=user,creation_date=datetime.datetime.now())
        return wish


class Wish(models.Model):
    url = models.URLField()
    name = models.CharField(max_length=500)
    website_name = models.CharField(max_length=500)
    website_url = models.URLField()
    price = models.FloatField()
    picture = models.URLField()
    creation_date = models.DateTimeField()
    user = models.ForeignKey(BdayAppUser)
    objects = WishManager()
    class Meta:
        ordering = ['-creation_date']

class ChatManager(models.Manager):
    def create_event_chat(self, event, user,wish = None,message_field=None, url_field=None, file_field = None, creation_date = datetime.datetime.now()):
        if message_field is None and url_field is None and file_field is None:
            pass
        else:
            event = self.create(event=event,wish = wish,message_field = message_field, url_field = url_field, file_field = file_field, user=user,creation_date = creation_date)
            return event

class EventChat(models.Model):
    event = models.ForeignKey(Event)
    message_field = models.CharField(max_length=100,null=True)
    creation_date = models.DateTimeField()
    url_field = models.URLField(null=True)
    file_field = models.FilePathField(null=True)
    wish = models.ForeignKey(Wish,null=True)
    user = models.ForeignKey(BdayAppUser)
    objects = ChatManager()
