from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<booking_id>\w+)/(?P<user_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/location/(?P<booking_id>\w+)/(?P<user_id>\w+)/$', consumers.LocationConsumer.as_asgi()),
]
