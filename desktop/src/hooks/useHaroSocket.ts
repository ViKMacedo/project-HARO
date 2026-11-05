import { useEffect, useRef, useState } from "react";
import type { HaroEvent } from "../types/types";
const WS_URL = "ws://127.0.0.1:8000/events";
export function useHaroSocket(onEvent: (event: HaroEvent) => void) {
  const [connected, setConnected] = useState(false);
  const handler = useRef(onEvent);
  handler.current = onEvent; // sempre usa a versão mais recente da função
  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: number | undefined;
    let stopped = false;
    const connect = () => {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => setConnected(true);
      ws.onmessage = (msg) => {
        try {
          handler.current(JSON.parse(msg.data));
        } catch {
          console.warn("Evento inválido:", msg.data);
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!stopped) timer = window.setTimeout(connect, 1500);
      };
      ws.onerror = () => ws?.close();
    };
    connect();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
      ws?.close();
    };
  }, []);
  return connected;
}
