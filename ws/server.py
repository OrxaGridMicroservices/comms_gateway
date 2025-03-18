from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging
import json
from typing import Dict, Set, Tuple

app = FastAPI()
logging.basicConfig(level=logging.INFO)

connected_clients = set()  # Store active WebSocket connections

@app.websocket("/ws")  # Make sure your client connects to "/ws"
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections."""

    logging.info(f"Incoming WebSocket request from {websocket.client}")

    await websocket.accept()  # Accept the WebSocket connection
    connected_clients.add(websocket)
    logging.info(f"New client connected: {websocket.client}")

    try:
        
        while True:
            # Receive data from Fledge
            data = await websocket.receive_text()
            payload = json.loads(data)
            logging.info(f"Received payload from Fledge: {json.dumps(payload, indent=2)}")
            
            # Broadcast to all connected clients
            await broadcast(json.dumps(payload))
    
    except WebSocketDisconnect:
        logging.warning(f"Client disconnected: {websocket.client}")
        connected_clients.remove(websocket)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
    finally:
        connected_clients.discard(websocket)
        logging.info("WebSocket connection closed")

async def broadcast(message: str):
    """Sends a message to all connected clients."""
    for client in connected_clients.copy():
        try:
            await client.send_text(message)
        except:
            connected_clients.discard(client)  # Remove disconnected clients

conn_clients: Dict[Tuple[str, str], Set[WebSocket]] = {}

@app.websocket("/ws/{asset}/{topic}")
async def websocket_endpoint(websocket: WebSocket, asset: str, topic: str):
    """Handles WebSocket connections for specific asset and topic."""
    await websocket.accept()
    client_key = (str(asset), topic)
    
    if client_key not in conn_clients:
        conn_clients[client_key] = set()
    conn_clients[client_key].add(websocket)
    
    logging.info(f"Client connected: asset={asset}, topic={topic}")

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            logging.info(f"Received payload from Fledge: {json.dumps(payload, indent=2)}")
            
            # Broadcast to all connected clients
            await broadcast_message(json.dumps(payload))
    except WebSocketDisconnect:
        logging.info(f"Client disconnected: asset={asset}, topic={topic}")
        conn_clients[client_key].remove(websocket)
        if not conn_clients[client_key]:
            del conn_clients[client_key]
    except Exception as e:
        logging.error(f"Error: {e}")
        conn_clients[client_key].remove(websocket)
        if not conn_clients[client_key]:
            del conn_clients[client_key]


async def broadcast_message(message: str):
    """Broadcasts messages to clients subscribed to specific asset and topic combinations."""
    try:
        payload_list = json.loads(message)
        
        for payload in payload_list:
            asset = payload.get("asset")
            readings = payload.get("readings", {})
            topic = readings.get("topic")
            
            if not asset or not topic:
                logging.warning("Payload missing asset or topic; skipping this payload.")
                continue

            client_key = (asset, topic.split("/")[1])
            if client_key in conn_clients:
                for client in conn_clients[client_key].copy():
                    try:
                        await client.send_text(json.dumps(readings))
                    except Exception as e:
                        logging.error(f"Failed to send message to client: {e}")
                        conn_clients[client_key].remove(client)
                # Clean up empty client sets
                if not conn_clients[client_key]:
                    del conn_clients[client_key]
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON message: {e}")
    except Exception as e:
        logging.error(f"Error in broadcast: {e}")
