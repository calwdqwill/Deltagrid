"""WebSocket streaming manager for real-time market data.

Connects to exchange WebSockets, normalizes events, and broadcasts
to connected frontend clients. Coexists with REST polling — stream
data is display-only overlay.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/!ticker@arr"


@dataclass
class NormalizedStreamEvent:
    """Unified ticker event for all exchanges."""
    event_type: str  # 'ticker'
    symbol: str
    price: float
    price_change_24h_pct: Optional[float] = None
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    source: str = "binance"
    timestamp: Optional[int] = None


class WebSocketManager:
    """Manages exchange streams and client broadcasts.

    Phase 4: Binance public ticker stream only.
    """

    def __init__(self):
        self.clients: list[WebSocket] = []
        self._exchange_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect_client(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.clients.append(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

    async def disconnect_client(self, websocket: WebSocket) -> None:
        if websocket in self.clients:
            self.clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def start(self) -> None:
        """Start exchange stream ingestion."""
        if self._running:
            return
        self._running = True
        self._exchange_task = asyncio.create_task(self._binance_stream_loop())
        logger.info("WebSocketManager started")

    async def stop(self) -> None:
        """Stop exchange stream ingestion."""
        self._running = False
        if self._exchange_task:
            self._exchange_task.cancel()
            try:
                await self._exchange_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocketManager stopped")

    async def _binance_stream_loop(self) -> None:
        """Connect to Binance WS and broadcast normalized events."""
        import websockets

        retry_delay = 1.0
        max_retry_delay = 30.0

        while self._running:
            try:
                async with websockets.connect(BINANCE_WS_URL) as ws:
                    logger.info("Binance WebSocket connected")
                    retry_delay = 1.0
                    while self._running:
                        raw = await asyncio.wait_for(ws.recv(), timeout=30.0)
                        data = json.loads(raw)
                        if isinstance(data, list):
                            for item in data[:20]:  # Limit to top 20 to avoid flooding
                                event = self._normalize_binance_ticker(item)
                                if event:
                                    await self._broadcast(event)
                        else:
                            event = self._normalize_binance_ticker(data)
                            if event:
                                await self._broadcast(event)
            except asyncio.TimeoutError:
                logger.warning("Binance WebSocket heartbeat timeout, reconnecting...")
            except websockets.ConnectionClosed:
                logger.warning("Binance WebSocket closed, reconnecting...")
            except Exception as e:
                logger.warning(f"Binance WebSocket error: {e}, reconnecting in {retry_delay}s...")

            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)

    def _normalize_binance_ticker(self, data: dict) -> Optional[NormalizedStreamEvent]:
        """Convert Binance 24hr ticker to normalized event."""
        try:
            symbol = data.get("s", "")
            if not symbol or not symbol.endswith("USDT"):
                return None
            return NormalizedStreamEvent(
                event_type="ticker",
                symbol=symbol.replace("USDT", "/USDT"),
                price=float(data.get("c", 0)),
                price_change_24h_pct=float(data.get("P", 0)),
                volume_24h=float(data.get("v", 0)),
                high_24h=float(data.get("h", 0)),
                low_24h=float(data.get("l", 0)),
                source="binance",
                timestamp=data.get("E"),
            )
        except (ValueError, TypeError):
            return None

    async def _broadcast(self, event: NormalizedStreamEvent) -> None:
        """Send normalized event to all connected clients."""
        if not self.clients:
            return
        payload = json.dumps(asdict(event), default=str)
        disconnected = []
        for client in self.clients:
            try:
                await client.send_text(payload)
            except Exception:
                disconnected.append(client)
        for client in disconnected:
            await self.disconnect_client(client)
