"""Streaming endpoints: WebSocket and SSE fallback.

Phase 4: Real-time price stream as overlay to polling baseline.
"""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.schemas.common import ApiResponse
from app.services.streaming.websocket_manager import WebSocketManager

router = APIRouter(prefix="/stream", tags=["stream"])

# Singleton manager shared across connections
_ws_manager = WebSocketManager()


@router.get("/config", response_model=ApiResponse)
async def stream_config():
    """Return stream configuration for frontend."""
    return ApiResponse(data={
        "websocket_url": "ws://127.0.0.1:8000/api/v1/stream/ws",
        "sse_url": "http://127.0.0.1:8000/api/v1/stream/sse",
        "supported_exchanges": ["binance"],
        "supported_channels": ["ticker"],
        "fallback_to_rest": True,
    })


@router.websocket("/ws")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time normalized ticker events."""
    await _ws_manager.connect_client(websocket)
    await _ws_manager.start()
    try:
        while True:
            # Keep connection alive, wait for client messages (e.g. ping/subscribe)
            message = await websocket.receive_text()
            try:
                msg = json.loads(message)
                if msg.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "ts": datetime.utcnow().isoformat()}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await _ws_manager.disconnect_client(websocket)


async def _sse_generator():
    """SSE generator that yields normalized ticker events."""
    queue: asyncio.Queue = asyncio.Queue()

    # Wrap queue into a dummy WebSocket-like object
    class DummyClient:
        async def send_text(self, text: str) -> None:
            await queue.put(text)

    client = DummyClient()
    await _ws_manager.connect_client(client)
    await _ws_manager.start()

    try:
        while True:
            payload = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield f"data: {payload}\n\n"
    except asyncio.TimeoutError:
        yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    finally:
        await _ws_manager.disconnect_client(client)


@router.get("/sse")
async def sse_stream():
    """SSE fallback endpoint for clients that cannot use WebSocket."""
    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
