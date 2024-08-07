import asyncio
import httpx
import json
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
import websockets
import logging
from models.envelope import Envelope
from services.forward_service import ForwardService
from services.config_service import ConfigService
from config.config import settings, logger

class WebSocketHandler:
    def __init__(self):
        self.websocket_clients = {}
        self.config_service = ConfigService()
        self.connection_id = self.config_service.get_connection_id()
        self.forward_service = ForwardService(settings.forward_service_url)

    async def websocket_endpoint(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.websocket_clients[connection_id] = {
            "websocket": websocket,
            "response_future": asyncio.Future()
        }
        try:
            while True:
                data = await websocket.receive_text()
                if connection_id in self.websocket_clients:
                    self.websocket_clients[connection_id]["response_future"].set_result(data)
                    self.websocket_clients[connection_id]["response_future"] = asyncio.Future()
        except WebSocketDisconnect:
            if connection_id in self.websocket_clients:
                del self.websocket_clients[connection_id]

    async def subscribe_to_proxy(self, proxy_url, connection_id):
        logger.error(f"listener: subscribe_to_proxy: Attempting to connect to proxy at {proxy_url} with connection ID {connection_id}")
        try:
            async with websockets.connect(proxy_url) as websocket:
                logger.error(f"Listener: Connected to proxy, sending registration with connection ID {connection_id}")
                await websocket.send(json.dumps({"action": "register", "connection_id": connection_id}))
                logger.info(f"Listener: Registered with proxy {proxy_url} using connection ID {connection_id}")

                try:
                    while True:
                        envelope_str = await websocket.recv()
                        logger.error(f"Listener: Received envelope from proxy: {envelope_str}")
                        envelope = Envelope.parse_raw(envelope_str)
                        try:
                            response = await self.forward_service.forward_request(envelope)
                            logger.error(f"Listener: Received response from forward_request: {response}")
                            await websocket.send(json.dumps(response))
                        except HTTPException as e:
                            logger.error(f"Listener: subscribe_to_proxy: Failed to forward: {envelope.endpoint_service_name}: {str(e)}")
                            await websocket.send(json.dumps(f"Listener: subscribe_to_proxy: Service Not Registered: {envelope.endpoint_service_name}: {str(e)}"))
                        except httpx.RequestError as e:
                            logger.error(f"Listener: Error forwarding request to {envelope.endpoint_service_name}: {str(e)}")
                            await websocket.send(json.dumps({"error": str(e)}))
                        except Exception as e:
                            await websocket.send(json.dumps(str(e)))
                            logger.error(f"Listener: Unhandled Exception: {str(envelope)}")
                except WebSocketDisconnect:
                    logger.error("Listener: WebSocket disconnected")
        except Exception as e:
            logger.error(f"Listener: Failed to connect to proxy at {proxy_url} with connection ID {connection_id} : {str(e)}")
