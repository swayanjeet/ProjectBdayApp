"""ProjectBdayApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Functionsviews
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from BdayApp import views
import logging
logger = logging.getLogger('django')
from BdayApp.UserProfileView import UserProfileView
from BdayApp.EventView import EventView
from BdayApp.UserView import UserView
from BdayApp.EventListView import EventListView
from BdayApp.EventAdminView import EventAdminView
from BdayApp.EventMembersView import EventMembersView
from BdayApp.FriendListView import FriendListView
from BdayApp.ReminderView import ReminderView
from BdayApp.ReminderListView import ReminderListView
from BdayApp.NotificationView import NotificationView
from BdayApp.NotificationListView import NotificationListView
from BdayApp.MessageView import MessageView
from BdayApp.MessageListView import MessageListView
from BdayApp.WishView import WishView
from BdayApp.WishListView import WishListView
from BdayApp.ChatListView import ChatListView
from BdayApp.UnreadChatBufferView import UnreadChatBufferView
from BdayApp.OtherLifeEventsListView import OtherLifeEventsListView
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^(?P<access_token>\w+)/user_profile', UserProfileView.as_view(), name='user_profile_view'),
    url(r'^(?P<access_token>\w+)/events/(?P<id>\d*)(/*)$',EventView.as_view(),name='event_view'),
    url(r'^(?P<access_token>\w+)/events/(?P<id>\d+)/admin',EventAdminView.as_view(),name='event_admin_view'),
    url(r'^(?P<access_token>\w+)/events/(?P<id>\d+)/members',EventMembersView.as_view(),name='event_members_view'),
    url(r'^(?P<access_token>\w+)/events/list$',EventListView.as_view(),name='event_list_view'),
    url(r'^(?P<access_token>[\w]*)(/*)user$',UserView.as_view(),name='user_view'),
    url(r'^(?P<access_token>\w+)/user/friends', FriendListView.as_view(), name='friend_list_view'),

    url(r'^(?P<access_token>\w+)/reminders/(?P<id>\d*)(/*)$',ReminderView.as_view(),name='reminder_view'),

    url(r'^(?P<access_token>\w+)/other_life_events/(?P<other_life_event_id>\d*)(/*)$', OtherLifeEventsListView.as_view(),name='other_life_events_view'),

    url(r'^(?P<access_token>\w+)/reminders/list$',ReminderListView.as_view(),name='reminder_list_view'),

    url(r'^(?P<access_token>\w+)/messages/(?P<id>\d*)(/*)$', MessageView.as_view(),name='message_view'),

    url(r'^(?P<access_token>\w+)/messages/list$', MessageListView.as_view(),name='message_list_view'),

    url(r'^(?P<access_token>\w+)/wish/(?P<id>\d*)(/*)$', WishView.as_view(),name='wish_view'),

    url(r'^(?P<access_token>\w+)/wish/list/(?P<id>\d*)(/*)$', WishListView.as_view(),name='wish_list_view'),

    url(r'^(?P<access_token>\w+)/notifications/(?P<id>[\d]*)(/*)$', NotificationView.as_view(), name='notification_view'),

    url(r'^(?P<access_token>\w+)/notifications/list$', NotificationListView.as_view(), name='notification_list_view'),

    url(r'^(?P<access_token>\w+)/events/(?P<id>\d+)/chat_list',ChatListView.as_view(), name='chat_list_view'),

    url(r'^(?P<access_token>\w+)/payment_portal/', views.payment_portal),

    url(r'^process_payment/', views.process_payment),

    url(r'^send_notification_for_date/', views.send_notification_for_date),

    url(r'^send_notification_to_friends_for_events/', views.send_notification_to_friends_for_events),

    url(r'^send_notification_for_wishlist/', views.send_notification_for_wishlist),

    url(r'^(?P<access_token>\w+)/send_address_request_notification/', views.send_address_request_notification),
           
    url(r'^(?P<access_token>\w+)/process_address_request', views.process_address_request),

    url(r'^get_giftstores/', views.get_giftstore_data),

    url(r'^(?P<access_token>\w+)/last_read_chat/(?P<event_id>\d+)/', UnreadChatBufferView.as_view(), name='unread_chat_buffer'),




] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
