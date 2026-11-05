# backend/main.py
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brain import build_system_prompt, split_emotion_tag
from state_machine import State, EXPRESSION_MAP, RING_MAP, can_transition


# ---------- Conexões WebSocket ----------
class ConnectionManager:
    """Guarda quem está conectado e envia mensagens a todos."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, payload: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
current_state = State.BOOT
state_lock = asyncio.Lock()


# ---------- Estado ----------
def state_event(state: State) -> dict:
    return {
        "type": "state_change",
        "state": state.value,
        "expression": EXPRESSION_MAP[state],
        "ring": RING_MAP[state],
    }


async def set_state(new_state: State, force: bool = False) -> bool:
    """Muda o estado respeitando o mapa de transições.
    Retorna False se a mudança não é permitida."""
    global current_state
    async with state_lock:
        if new_state == current_state:
            return True
        if not force and not can_transition(current_state, new_state):
            print(f"[estado] transição negada: {current_state.value} -> {new_state.value}")
            return False
        current_state = new_state
    await manager.broadcast(state_event(new_state))
    return True


# ---------- Aplicação ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda quando o servidor sobe: BOOT -> IDLE
    await set_state(State.IDLE)
    yield


app = FastAPI(title="HARO Backend", lifespan=lifespan)

# Permite que o app desktop (outra "origem") converse com o backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",    # servidor de desenvolvimento do Tauri/Vite
        "tauri://localhost",        # app empacotado (macOS/Linux)
        "http://tauri.localhost",   # app empacotado (Windows)
        "https://tauri.localhost",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Rotas básicas ----------
@app.get("/health")
async def health():
    return {"status": "ok", "state": current_state.value}


@app.post("/debug/state/{name}")
async def debug_state(name: str):
    """Força um estado, útil para testar as animações do corpo."""
    try:
        state = State(name.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Estado inválido: {name}")
    await set_state(state, force=True)
    return {"state": current_state.value}


@app.websocket("/events")
async def events_endpoint(ws: WebSocket):
    await manager.connect(ws)
    # Quem acabou de conectar precisa saber o estado atual imediatamente.
    await ws.send_json(state_event(current_state))
    try:
        while True:
            await ws.receive_text()  # mantém a conexão viva
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ---------- Conversa (sem IA, por enquanto) ----------
history: list[dict] = []   # memória curta da conversa
MAX_HISTORY = 20           # últimas 20 mensagens


class ChatIn(BaseModel):
    message: str


DEMO_REPLIES = [
    "[CURIOUS] Hmm, interessante! Me conta mais sobre isso.",
    "[HAPPY] Que bom ter companhia! Estou em modo demonstração.",
    "[CONFUSED] Não sei se entendi tudo, mas adorei a conversa.",
]


async def generate_reply(messages: list[dict]) -> str:
    # TODO(ia-local): trocar por chamada a um modelo local (Ollama) ou da nuvem
    await asyncio.sleep(1.2)   # simula o "pensar", para você ver o estado THINKING
    turns = sum(1 for m in messages if m["role"] == "user")
    return DEMO_REPLIES[(turns - 1) % len(DEMO_REPLIES)]


async def recover_from_error():
    await asyncio.sleep(3)
    await set_state(State.IDLE)


async def settle_after_talk(text: str):
    # Provisório: estima a duração da fala pelo tamanho do texto.
    # No Capítulo 8 isso é substituído pelo fim real do áudio.
    await asyncio.sleep(min(2 + len(text) * 0.06, 15))
    await set_state(State.AWAKE)


@app.post("/chat")
async def chat(body: ChatIn):
    text = body.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    if not await set_state(State.THINKING):
        raise HTTPException(status_code=409, detail="O HARO está ocupado")

    try:
        messages = [
            {"role": "system", "content": build_system_prompt()},
            *history,
            {"role": "user", "content": text},
        ]
        raw = await generate_reply(messages)
    except Exception as exc:
        await set_state(State.ERROR)
        asyncio.create_task(recover_from_error())
        raise HTTPException(status_code=502, detail=f"Falha ao gerar resposta: {exc}")

    emotion, reply = split_emotion_tag(raw)

    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply})
    del history[:-MAX_HISTORY]

    await set_state(State.TALK)
    await manager.broadcast({
        "type": "transcript",
        "text": reply,
        "emotion": emotion,
    })
    asyncio.create_task(settle_after_talk(reply))
    return {"reply": reply, "emotion": emotion}