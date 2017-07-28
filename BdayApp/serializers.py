from rest_framework import serializers
from BdayApp.models import *


class OtherLifeEventsSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherLifeEvents
        fields = ('name', 'date_of_event', 'created_date', 'type','id')

class CashOutCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = CashoutCard
        fields = ('type','terms_and_conditions','shipping_and_handling','brand_details','coupon_code','amount','created_date', 'id')

class UserSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    user_name = serializers.CharField(read_only=True,source='user_id.user_name')
    profile_id = serializers.CharField(read_only=True,source='user_id.profile_id')
    picture = serializers.URLField(read_only=True,source='user_id.picture')
    profile_type = serializers.CharField(read_only=True,source='user_id.profile_type')
    birthday = serializers.CharField(source='user_id.birthday')
    wallet_balance = serializers.CharField(source='user_wallet.balance',read_only=True)
    contact_privacy_field = serializers.CharField(source='user_id.contact_privacy_field', read_only=True)
    street_address = serializers.SerializerMethodField('return_street_address', read_only=True)
    address_line_2 = serializers.SerializerMethodField('return_address_line_2', read_only=True)
    city = serializers.SerializerMethodField('return_city', read_only=True)
    state = serializers.SerializerMethodField('return_state', read_only=True)
    pincode = serializers.SerializerMethodField('return_pincode', read_only=True)
    phone_number = serializers.SerializerMethodField('return_phone_number', read_only=True)
    first_name = serializers.CharField(source='user_id.first_name', read_only=True)
    last_name = serializers.CharField(source='user_id.last_name',read_only=True)
    other_life_events = OtherLifeEventsSerializer(many=True, read_only=True)
    cashout_cards_list = CashOutCardSerializer(many=True, read_only=True)

    def return_street_address(self, obj):
        if obj.user_id.contact_privacy_field == "PV":
            return ""
        else:
            return obj.user_id.street_address

    def return_address_line_2(self, obj):
        if obj.user_id.contact_privacy_field == "PV":
            return ""
        else:
            return obj.user_id.address_line_2

    def return_city(self, obj):
        if obj.user_id.contact_privacy_field == "PV":
            return ""
        else:
            return obj.user_id.city

    def return_state(self, obj):
        if obj.user_id.contact_privacy_field == "PV":
            return ""
        else:
            return obj.user_id.state

    def return_pincode(self, obj):
        if obj.user_id.contact_privacy_field == "PV":
            return ""
        else:
            return obj.user_id.pincode

    def return_phone_number(self, obj):
        if obj.user_id.contact_privacy_field == "PV":
            return ""
        else:
            return obj.user_id.phone_number

    class Meta:
        model = BdayAppUser
        fields = ('email_id', 'id', 'creation_date', 'user_name', 'profile_id', 'picture', 'profile_type', 'birthday', 'wallet_balance', 'contact_privacy_field', 'street_address', 'address_line_2', 'city', 'state', 'pincode', 'first_name', 'last_name', 'phone_number', 'other_life_events')

class UserProfileSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='user.id', read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'user_name', 'user','profile_type', 'picture', 'birthday', 'street_address', 'address_line_2' , 'city', 'state', 'pincode' , 'address_privacy_field', 'first_name', 'last_name','gender','phone_number','creation_date')


class EventSerializer(serializers.ModelSerializer):
    last_chat = serializers.SerializerMethodField('return_last_read_chat')
    total_number_of_unread_chats = serializers.SerializerMethodField('return_total_number_of_unread_chats')
    event_id = serializers.IntegerField(source='id', read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    wallet_balance = serializers.CharField(source='event_wallet.balance',read_only=True)

    def return_last_read_chat(self, obj):
        last_chat = EventChat.objects.filter(event=obj).order_by('-creation_date').first()
        serializer = ChatListSerializer(last_chat)
        return serializer.data

    def return_total_number_of_unread_chats(self, obj):
        user = UserProfile.objects.get(profile_id__exact='1069321953161548').user
        last_chat = UnreadChatBuffer.objects.get(event=obj, user=user).last_read_chat
        data = EventChat.objects.filter(event=obj).order_by('-creation_date')
        count = 0
        if data is None:
            return 0
        elif last_chat is None:
            return data.count()
        else:
            for chat in data:
                if last_chat.id > chat.id:
                        pass
                else:
                    count += 1
        return count

    class Meta:
        model = Event
        fields = ('event_id', 'name', 'creation_date', 'start_date', 'end_date', 'picture', 'wallet_balance','type','last_chat','total_number_of_unread_chats')


class ReminderSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    associated_event = serializers.IntegerField(source='associated_event.id')
    created_by = serializers.IntegerField(source='user.id',read_only=True)
    reminder_for = UserSerializer()

    class Meta:
        model = Reminder
        fields = ('id', 'picture', 'picture_file','name', 'reminder_date', 'event_associated_flag', 'associated_event', 'created_by', 'creation_date','type', 'reminder_for')


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
    event = EventSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ('id','message','associated_user','url','is_read','read_date','type','event_reminder_type','event_for_user','creation_date','event')



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
    wish = WishSerializer(read_only=True)
    creation_date = serializers.DateTimeField(read_only=True)
    user = UserSerializer(read_only=True)
    read = serializers.SerializerMethodField('is_chat_read')

    def is_chat_read(self, chat):
        user = UserProfile.objects.get(profile_id__exact='1069321953161548').user
        last_read_chat = UnreadChatBuffer.objects.get(event=chat.event, user=user).last_read_chat
        if last_read_chat is not None:
                if last_read_chat.id > chat.id:
                    return True
        else:
            return False

    class Meta:
        model = EventChat
        fields = ('id', 'message_field', 'url_field', 'file_field', 'wish', 'event', 'user', 'type','creation_date','read')

class UnreadChatBufferSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)
    event = EventSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    last_read_chat = ChatListSerializer()

    class Meta:
        model = UnreadChatBuffer
        fields = ('id','event','user','last_read_chat')

