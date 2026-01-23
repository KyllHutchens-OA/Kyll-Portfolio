"""
AFL Analytics Agent - Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import logging

__version__ = "0.1.0"

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config=None):
    """Create and configure the Flask application."""

    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

    if config:
        app.config.update(config)

    # Enable CORS
    CORS(app)

    # Initialize SocketIO
    socketio.init_app(app)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Register blueprints
    from app.api import routes
    app.register_blueprint(routes.bp)

    # Register WebSocket handlers
    from app.api import websocket

    return app
