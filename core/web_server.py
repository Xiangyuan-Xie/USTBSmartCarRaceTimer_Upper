import asyncio
import json
import os
from threading import Thread

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

# Suppress uvicorn logs
# logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
# logging.getLogger("uvicorn.access").setLevel(logging.ERROR)


class WebServer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebServer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.app = FastAPI()
        self.connected_clients = []
        self.loop = None
        self.thread = None
        self.latest_data = {}

        # Setup paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        web_dir = os.path.join(base_dir, "web")
        static_dir = os.path.join(web_dir, "static")
        templates_dir = os.path.join(web_dir, "templates")

        # Ensure directories exist
        os.makedirs(static_dir, exist_ok=True)
        os.makedirs(templates_dir, exist_ok=True)

        # Mount static files
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        self.templates = Jinja2Templates(directory=templates_dir)

        # Routes
        @self.app.get("/", response_class=HTMLResponse)
        async def get_home(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.append(websocket)
            try:
                # Send initial data if available
                if self.latest_data:
                    await websocket.send_text(json.dumps(self.latest_data))

                while True:
                    await websocket.receive_text()  # Keep connection open
            except WebSocketDisconnect:
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)
            except Exception:
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)

        self._initialized = True

    def start(self, host="0.0.0.0", port=8000):
        if self.thread is None:
            self.thread = Thread(target=self._run, args=(host, port), daemon=True)
            self.thread.start()

    def _run(self, host, port):
        # Create a new event loop for the thread
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            config = uvicorn.Config(self.app, host=host, port=port, loop="asyncio", log_level="error")
            server = uvicorn.Server(config)
            self.loop.run_until_complete(server.serve())
        except Exception as e:
            logger.error(f"Web server failed to start: {e}")

    def broadcast(self, data):
        """Broadcast data to all connected clients"""
        self.latest_data = data
        if self.loop and self.connected_clients and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast_async(data), self.loop)

    async def _broadcast_async(self, data):
        json_data = json.dumps(data)
        to_remove = []
        for client in self.connected_clients:
            try:
                await client.send_text(json_data)
            except Exception:
                to_remove.append(client)

        for client in to_remove:
            if client in self.connected_clients:
                self.connected_clients.remove(client)
