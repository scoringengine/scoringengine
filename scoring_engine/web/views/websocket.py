from flask_socketio import emit, join_room, leave_room
from scoring_engine.web import socketio
from scoring_engine.logger import logger


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.debug(f"Client connected")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.debug(f"Client disconnected")


@socketio.on('join_scoreboard')
def handle_join_scoreboard():
    """Subscribe client to scoreboard updates"""
    join_room('scoreboard')
    logger.debug("Client joined scoreboard room")
    emit('joined', {'room': 'scoreboard'})


@socketio.on('leave_scoreboard')
def handle_leave_scoreboard():
    """Unsubscribe client from scoreboard updates"""
    leave_room('scoreboard')
    logger.debug("Client left scoreboard room")
    emit('left', {'room': 'scoreboard'})
