from rest_framework import serializers
from BdayApp.models import *


class UserSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    user_name = serializers.CharField(read_only=True,source='user_id.user_name')
    profile_id = serializers.CharField(read_only=True,source='user_id.profile_id')
    picture = serializers.URLField(read_only=True, source='user_id.picture')
    profile_type = serializers.CharField(read_only=True,source='user_id.profile_type')
    birthday = serializers.CharField(source='user_id.birthday')
    wallet_balance = serializers.CharField(source='user_wallet.balance',read_only=True)

    class Meta:
        model = BdayAppUser
        fields = ('email_id', 'id', 'creation_date', 'user_name', 'profile_id', 'picture', 'profile_type', 'birthday', 'wallet_balance')


class UserProfileSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='user.id', read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    address_privacy_field = serializers.CharField()

    class Meta:
        model = UserProfile
        fields = ('id', 'user_name', 'profile_type', 'picture', 'birthday', 'address', 'address_privacy_field', 'first_name', 'last_name','gender','phone_number','creation_date')


class EventSerializer(serializers.ModelSerializer):

    event_id = serializers.IntegerField(source='id', read_only=True)
    wallet_balance = serializers.CharField(source='event_wallet.balance',read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Event
        fields = ('event_id', 'name', 'creation_date', 'start_date', 'end_date', 'picture', 'wallet_balance')


class ReminderSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    associated_event = serializers.IntegerField(source='associated_event.id')
    created_by = serializers.IntegerField(source='user.id',read_only=True)
    reminder_for = UserSerializer()

    class Meta:
        model = Reminder
        fields = ('id', 'picture', 'name', 'reminder_date', 'event_associated_flag', 'associated_event', 'created_by', 'creation_date','type', 'reminder_for')


class MessageSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    to_field = UserSerializer(read_only=True)
    from_field = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ('id', 'message','to_field','from_field','creation_date','is_read','read_date')


class NotificationSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    associated_user = UserSerializer(read_only=True)
    event_for_user = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ('id','message','associated_user','url','is_read','read_date','type','event_reminder_type','event_for_user','creation_date')


class WishSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    user = UserSerializer(read_only=True)
    name = serializers.CharField(read_only=True, max_length=500)
    website_name = serializers.CharField(read_only=True,max_length=500)
    price = serializers.CharField(read_only=True,max_length=500)
    picture = serializers.URLField(read_only=True)
    website_url = serializers.URLField(read_only=True)
    url = serializers.URLField(read_only=True)


    class Meta:
        model = Wish
        fields = ('id', 'url', 'name', 'website_name', 'website_url', 'price', 'picture', 'creation_date', 'user')

class ChatListSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    message_field = serializers.CharField(read_only=True)
    url_field = serializers.URLField(read_only=True)
    file_field = serializers.FilePathField(read_only=True,path='/Media/')
    wish = WishSerializer(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventChat
        fields = ('id', 'message_field', 'url_field', 'file_field', 'wish', 'event', 'user', 'type','creation_date')

class UnreadChatBufferSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    event = EventSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    last_read_chat = ChatListSerializer()

    class Meta:
        model = UnreadChatBuffer
        fields = ('id','event','user','last_read_chat')

class FileTest(serializers.ModelSerializer):

    file_field = serializers.ImageField()

    class Meta:
        model = FileTestMode
        fields = ('file_field','char_field')