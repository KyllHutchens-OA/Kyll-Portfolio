"""
AFL Analytics Agent - API Routes
"""
from flask import Blueprint, jsonify, request
from app.data.database import Session
from app.data.models import Match, Team
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        session = Session()
        match_count = session.query(Match).count()
        team_count = session.query(Team).count()
        session.close()

        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'matches': match_count,
            'teams': team_count
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@bp.route('/chat/message', methods=['POST'])
async def chat_message():
    """
    Handle chat messages (REST endpoint for non-streaming).
    For streaming, use WebSocket instead.
    """
    try:
        data = request.get_json()
        message = data.get('message')
        conversation_id = data.get('conversation_id')

        if not message:
            return jsonify({'error': 'Message required'}), 400

        # Import agent
        from app.agent import agent

        # Run agent workflow
        final_state = await agent.run(message, conversation_id)

        # Return response
        return jsonify({
            'conversation_id': conversation_id or 'new-conv-id',
            'status': 'complete',
            'response': final_state.get('natural_language_summary', 'Unable to process query'),
            'confidence': final_state.get('confidence', 0.0),
            'sources': final_state.get('sources', [])
        }), 200

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get conversation history."""
    # TODO: Implement conversation retrieval
    return jsonify({
        'conversation_id': conversation_id,
        'messages': [],
        'created_at': None
    }), 200
