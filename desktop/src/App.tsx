import { useState } from "react";
import { Face } from "./components/Face";
import { useHaroSocket } from "./hooks/useHaroSocket";
import type { HaroEvent } from "./types/types";
import "./App.css";
const API = "http://127.0.0.1:8000";
export default function App() {
  const [expression, setExpression] = useState("IDLE");
  const [ring, setRing] = useState("dim_idle");
  const [emotion, setEmotion] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [input, setInput] = useState("");
  const connected = useHaroSocket((event: HaroEvent) => {
    if (event.type === "state_change") {
      setExpression(event.expression);
      setRing(event.ring);
      setEmotion(null); // a emoção vale só durante a fala atual
    } else if (event.type === "transcript") {
      setText(event.text);
      setEmotion(event.emotion);
    }
  });
  // Sem conexão com o cérebro, o corpo mostra OFFLINE.
  // Falando com uma emoção escolhida pela IA, a emoção vence a expressão genérica.
  let shownExpression = expression;
  let shownRing = ring;
  if (!connected) {
    shownExpression = "OFFLINE";
    shownRing = "red_slow_pulse";
  } else if (expression === "TALKING" && emotion) {
    shownExpression = emotion;
  }
  async function send() {
    const message = input.trim();
    if (!message) return;
    setInput("");
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setText(err.detail ?? "Algo deu errado.");
      }
    } catch {
      setText("Haro não consegue falar, Haro offline.");
    }
  }
  return (
    <div className="stage">
      <Face expression={shownExpression} ring={shownRing} />
      {text && <div className="bubble">{text}</div>}
      <div className="chat">
        <input
          value={input}
          placeholder="Fale com o HARO..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button onClick={send}>Enviar</button>
      </div>
    </div>
  );
}
