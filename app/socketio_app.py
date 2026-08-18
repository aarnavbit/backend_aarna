import socketio
from app.services.game_state import game_state

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

active_connections = 0

@sio.event
async def connect(sid, environ):
    global active_connections
    active_connections += 1
    game_state.set_connected_clients(active_connections)
    
    # Send current game state to the newly connected client
    await sio.emit('game_state', game_state.get_state(), to=sid)
    # Broadcast updated client count to all
    await sio.emit('game_state', game_state.get_state())
    await sio.emit('connected_clients', {'count': active_connections})

@sio.event
async def disconnect(sid):
    global active_connections
    active_connections -= 1
    game_state.set_connected_clients(active_connections)
    await sio.emit('game_state', game_state.get_state())
    await sio.emit('connected_clients', {'count': active_connections})

async def broadcast_game_started():
    await sio.emit('game_started', game_state.get_state())

async def broadcast_game_ended():
    await sio.emit('game_ended', game_state.get_state())

async def broadcast_lobby_reset():
    await sio.emit('game_state', game_state.get_state())
    await sio.emit('leaderboard_reset', {})

async def broadcast_leaderboard_update():
    await sio.emit('leaderboard_update', {})
