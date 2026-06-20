import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .models import ChatMessage
from django.utils import timezone
from rest_framework.exceptions import ValidationError

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    
    Connect: ws://localhost:8000/ws/chat/{booking_id}/{user_id}/?token=JWT_TOKEN
    """

    async def connect(self):
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'booking_{self.booking_id}_chat'
        self.user = None  # Initialize user attribute

        # Extract JWT token from query string
        # Format: ws://localhost:8000/ws/chat/{booking_id}/{user_id}/?token=JWT_TOKEN
        query_string = self.scope['query_string'].decode()
        token = None
        
        if 'token=' in query_string:
            token = query_string.split('token=')[-1].split('&')[0]
        
        # Verify user and validate JWT token
        user_data = await self.verify_user_and_token(self.user_id, token)
        if not user_data:
            await self.close()
            return

        self.user = user_data

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Only discard if connection was accepted (user authenticated)
        if self.user is not None:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get('message', '')
        recipient_id = data.get('recipient_id')

        if not message_text or not recipient_id:
            await self.send(text_data=json.dumps({
                'error': 'Message and recipient_id required'
            }))
            return

        # Save message to database
        message = await self.save_message(self.user_id, recipient_id, self.booking_id, message_text)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender_id': self.user_id,
                'recipient_id': recipient_id,
                'message_id': message.id,
                'timestamp': message.created_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        """Receive message from room group"""
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'recipient_id': event['recipient_id'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def verify_user_and_token(self, user_id, token):
        """Verify user exists and JWT token is valid"""
        try:
            if not token:
                return None
            
            # Validate JWT token
            jwt_auth = JWTAuthentication()
            from rest_framework.request import Request
            from rest_framework.test import APIRequestFactory
            
            # Create a fake request to validate token
            factory = APIRequestFactory()
            request = factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
            
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            # Verify user_id matches
            if user.id != int(user_id):
                return None
            
            return {
                'id': user.id,
                'full_name': user.full_name,
            }
        except (InvalidToken, AuthenticationFailed, ValidationError, ValueError, TypeError):
            return None
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, sender_id, recipient_id, booking_id, text):
        """Save chat message to database"""
        try:
            sender = User.objects.get(id=sender_id)
            recipient = User.objects.get(id=recipient_id)
            message = ChatMessage.objects.create(
                sender=sender,
                recipient=recipient,
                booking_id=booking_id,
                text=text
            )
            return message
        except User.DoesNotExist:
            raise Exception("User not found")


class LocationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time location tracking during ride.
    Provider shares live location with customer in real-time.
    
    Connect: ws://localhost:8000/ws/location/{booking_id}/{user_id}/?token=JWT_TOKEN
    
    Provider sends location:
    {
        "type": "location_update",
        "latitude": 25.204800,
        "longitude": 55.270800,
        "accuracy": 5.0
    }
    
    Customer receives:
    {
        "type": "location_update",
        "user_id": 90,
        "user_type": "provider",
        "user_name": "John",
        "latitude": 25.204800,
        "longitude": 55.270800,
        "accuracy": 5.0,
        "timestamp": "2026-06-20T12:30:45.123456Z"
    }
    """

    async def connect(self):
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'booking_{self.booking_id}_location'
        # Initialize attributes to prevent errors if connection fails
        self.user_type = None
        self.user_full_name = None

        # Extract JWT token from query string
        # Format: ws://localhost:8000/ws/location/{booking_id}/{user_id}/?token=JWT_TOKEN
        query_string = self.scope['query_string'].decode()
        token = None
        
        if 'token=' in query_string:
            token = query_string.split('token=')[-1].split('&')[0]
        
        # Verify user and validate JWT token
        user_data = await self.verify_user_and_token(self.user_id, token)
        if not user_data:
            await self.close()
            return

        self.user_type = user_data['role']  # 'provider' or 'customer'
        self.user_full_name = user_data['full_name']

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'action': 'joined',
                'user_id': self.user_id,
                'user_type': self.user_type,
                'user_name': self.user_full_name,
                'timestamp': timezone.now().isoformat(),
            }
        )

    async def disconnect(self, close_code):
        # Only notify if connection was accepted (user authenticated)
        if self.user_type is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'action': 'left',
                    'user_id': self.user_id,
                    'user_type': self.user_type,
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            # Leave the room group
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')

            if msg_type == 'location_update':
                latitude = data.get('latitude')
                longitude = data.get('longitude')
                accuracy = data.get('accuracy')

                if latitude is None or longitude is None:
                    await self.send(text_data=json.dumps({
                        'error': 'latitude and longitude required'
                    }))
                    return

                # Save location update to database
                await self.save_location_update(
                    booking_id=self.booking_id,
                    user_id=self.user_id,
                    user_type=self.user_type,
                    latitude=latitude,
                    longitude=longitude,
                    accuracy=accuracy
                )

                # Broadcast location to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'location_update_broadcast',
                        'user_id': self.user_id,
                        'user_type': self.user_type,
                        'user_name': self.user_full_name,
                        'latitude': latitude,
                        'longitude': longitude,
                        'accuracy': accuracy,
                        'timestamp': timezone.now().isoformat(),
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))

    async def location_update_broadcast(self, event):
        """Receive location update from room group and send to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'user_id': event['user_id'],
            'user_type': event['user_type'],
            'user_name': event['user_name'],
            'latitude': float(event['latitude']),
            'longitude': float(event['longitude']),
            'accuracy': float(event['accuracy']) if event['accuracy'] else None,
            'timestamp': event['timestamp'],
        }))

    async def user_status(self, event):
        """Receive user status change (joined/left) and broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'action': event['action'],
            'user_id': event['user_id'],
            'user_type': event['user_type'],
            'user_name': event.get('user_name', 'Unknown'),
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def verify_user_and_token(self, user_id, token):
        """Verify user exists and JWT token is valid"""
        try:
            if not token:
                return None
            
            # Validate JWT token
            jwt_auth = JWTAuthentication()
            
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            # Verify user_id matches
            if user.id != int(user_id):
                return None
            
            return {
                'id': user.id,
                'full_name': user.full_name,
                'role': user.role,
            }
        except (InvalidToken, AuthenticationFailed, ValidationError, ValueError, TypeError):
            return None
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_location_update(self, booking_id, user_id, user_type, latitude, longitude, accuracy):
        """Save location update to database"""
        try:
            from apps.bookings.models import Booking
            booking = Booking.objects.get(id=booking_id)
            
            # Update provider's current location
            if user_type == 'provider' and booking.provider:
                booking.provider.current_latitude = latitude
                booking.provider.current_longitude = longitude
                booking.provider.save()
            
            # Create location history record
            from .models import LocationHistory
            LocationHistory.objects.create(
                booking_id=booking_id,
                user_id=user_id,
                user_type=user_type,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy
            )
        except Exception as e:
            print(f"Error saving location: {str(e)}")

