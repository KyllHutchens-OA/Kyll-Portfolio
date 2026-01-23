"""
AFL Analytics Agent - WebSocket Handlers
"""
from app import socketio
import logging

logger = logging.getLogger(__name__)


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected")


@socketio.on('chat_message')
def handle_chat_message(data):
    """
    Handle incoming chat messages via WebSocket.

    Expected data:
        {
            "message": "user query",
            "conversation_id": "uuid" (optional)
        }
    """
    logger.info(f"Received message: {data}")

    try:
        user_query = data.get('message')
        conversation_id = data.get('conversation_id')

        if not user_query:
            socketio.emit('error', {'message': 'No message provided'})
            return

        # Import agent
        from app.agent import agent
        import asyncio
        import time

        # Manual thinking updates (simplified for now)
        socketio.emit('thinking', {'step': '🔍 Received your question...'})
        time.sleep(0.5)

        socketio.emit('thinking', {'step': '🤖 Starting agent workflow...'})
        time.sleep(0.3)

        # Run the async agent in a synchronous context
        logger.info(f"Running agent for query: {user_query}")
        final_state = asyncio.run(agent.run(user_query, conversation_id))
        logger.info(f"Agent completed, final state keys: {final_state.keys()}")

        # Send visualization if available
        if final_state.get('visualization_spec'):
            socketio.emit('visualization', {
                'spec': final_state['visualization_spec']
            })

        # Send response
        if final_state.get('natural_language_summary'):
            socketio.emit('response', {
                'text': final_state['natural_language_summary'],
                'confidence': final_state.get('confidence', 0.0),
                'sources': final_state.get('sources', [])
            })
        else:
            socketio.emit('response', {
                'text': 'I was unable to process your query.',
                'confidence': 0.0
            })

        # Send completion
        socketio.emit('complete', {})

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('error', {'message': f'Error: {str(e)}'})
