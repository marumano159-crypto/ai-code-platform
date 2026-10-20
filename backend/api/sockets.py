from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Stores active connections mapped to a specific room ID
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            # Clean up empty rooms to prevent memory leaks on the server
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    # PROFESSIONAL UPDATE: Added the 'sender' parameter
    async def broadcast_to_room(self, message: str, room_id: str, sender: WebSocket):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                # ONLY send the code update to OTHER users, never echo back to the sender
                if connection != sender:
                    try:
                        await connection.send_text(message)
                    except Exception:
                        # Fallback to handle abruptly dropped connections
                        pass

manager = ConnectionManager()

@router.websocket("/ws/code/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            # Wait for a user to type something
            data = await websocket.receive_text()
            # Instantly broadcast to everyone else in the room, passing the sender
            await manager.broadcast_to_room(data, room_id, sender=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)