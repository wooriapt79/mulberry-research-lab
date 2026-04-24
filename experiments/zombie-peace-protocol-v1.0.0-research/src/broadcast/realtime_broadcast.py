"""
Real-time Broadcast Module

This module implements Socket.IO + A2A hybrid broadcasting for real-time synchronization
and message dissemination among agents.
"""

import socketio
import logging
import socket # For ConnectionRefusedError

logger = logging.getLogger(__name__)

class BroadcastClient:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BroadcastClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, config=None):
        if not self._initialized:
            self.sio = socketio.Client()
            self.server_url = config.get('server_url', 'http://localhost:5000') if config else 'http://localhost:5000'

            # Register event handlers
            self.sio.on('connect', self._on_connect)
            self.sio.on('disconnect', self._on_disconnect)

            BroadcastClient._initialized = True

    def _on_connect(self):
        logger.info('Socket.IO connection established!')

    def _on_disconnect(self):
        logger.info('Socket.IO disconnected.')

    def establish_connection(self):
        """Establishes a real-time connection using Socket.IO."""
        logger.info(f"Attempting to connect to Socket.IO server at {self.server_url}")
        try:
            self.sio.connect(self.server_url)
        except (socketio.exceptions.ConnectionError, socket.error) as e:
            logger.error(f"Failed to connect to Socket.IO server at {self.server_url}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while connecting to Socket.IO server at {self.server_url}: {e}")

    def broadcast_message(self, event, data):
        """Broadcasts messages to agents in real-time."""
        if self.sio.connected:
            self.sio.emit(event, data)
            logger.info(f"Broadcasting event '{event}' with data: {data}")
        else:
            logger.warning("Not connected to Socket.IO server. Cannot broadcast.")

    def listen_for_messages(self):
        """Placeholder for listening logic. Real implementation would involve @sio.on decorators."""
        logger.info("Listening for Socket.IO messages... (requires running server and specific handlers)")

    def close_connection(self):
        """Closes the Socket.IO connection."""
        if self.sio.connected:
            self.sio.disconnect()
        else:
            logger.info("Not connected to Socket.IO server.")

# Module-level functions now interact with a singleton BroadcastClient instance
_broadcast_client_instance = None

def get_broadcast_client(config=None):
    global _broadcast_client_instance
    if _broadcast_client_instance is None:
        _broadcast_client_instance = BroadcastClient(config)
    return _broadcast_client_instance

def establish_connection(config=None):
    client = get_broadcast_client(config)
    client.establish_connection()

def broadcast_message(event, data):
    client = get_broadcast_client()
    client.broadcast_message(event, data)

def listen_for_messages():
    client = get_broadcast_client()
    client.listen_for_messages()

def close_connection():
    client = get_broadcast_client()
    client.close_connection()
