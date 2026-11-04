import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from state_machine import State, EXPRESSION_MAP, RING_MAP, can_transition

class ConnectionManager:
    """ Guarda quem está conectado e envia uma mensagem a todos os outros """
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

def state_event(state: State) -> dict:
    return{
        "type": "state_change",
        "state": "state.value",
        "expression": EXPRESSION_MAP[state],
        "ring": RING_MAP[state]
    }

async def set_state (new_state: State, force: bool = False) -> bool:
    """"Muda estado e respeita o mapa de transição
    retornará FALSE caso a mudança não seja perimitida"""
    global current_state
    async with state_lock:
        if new_state == current_state:
            return True
        if not force and not can_transition(current_state, new_state):
            print(f"[estado] transição negada:{current_state.value} -> {new_state.value}")
            return False
        current_state = new_state
    await manager.broadcast(state_event(new_state))
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # roda quando o server sobe BOOT -> IDLE
    await set_state(State.IDLE)
    yield

app = FastAPI(title="HARO Backend", lifespan=lifespan)

# Permire de o App Desktop converse com o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost1420",     #servidor Tauri/Vite
        "tauri://localhost",        #app empacotado (macOS/Linux)
        "http://tauri.localhost",   #app empacotado (Windows)
        "https://tauri.localhost",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return{"status": "ok", "state": current_state.value}

@app.post("/debug/state/{name}")
async def debug_state(name: str):
    """"Força um estado, teste de animações"""
    try:
        state = State(name.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"ESTADO INVÁLIDO{name}")
    await set_state(state, force=True)
    return {"state: current_state.value"}

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
