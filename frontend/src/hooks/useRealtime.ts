"use client";

import { useEffect, useRef } from "react";
import { useStreamStore } from "@/stores/streamStore";

const WS_URL = "ws://127.0.0.1:8000/api/v1/stream/ws";
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useRealtime(enabled: boolean = true) {
  const { setConnected, addTick, setLastPing } = useStreamStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled) return;

    function connect() {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
          reconnectCountRef.current = 0;
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "pong") {
              setLastPing(Date.now());
              return;
            }
            if (data.event_type === "ticker") {
              addTick({
                eventType: data.event_type,
                symbol: data.symbol,
                price: data.price,
                priceChange24hPct: data.price_change_24h_pct ?? null,
                volume24h: data.volume_24h ?? null,
                high24h: data.high_24h ?? null,
                low24h: data.low_24h ?? null,
                source: data.source,
                timestamp: data.timestamp ?? null,
              });
            }
          } catch {
            // ignore malformed messages
          }
        };

        ws.onclose = () => {
          setConnected(false);
          wsRef.current = null;
          if (reconnectCountRef.current < MAX_RECONNECT_ATTEMPTS) {
            reconnectCountRef.current += 1;
            reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
          }
        };

        ws.onerror = () => {
          // onclose will handle reconnection
        };
      } catch {
        setConnected(false);
      }
    }

    connect();

    // Ping every 20s to keep connection alive
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: "ping" }));
      }
    }, 20000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [enabled, setConnected, addTick, setLastPing]);
}
