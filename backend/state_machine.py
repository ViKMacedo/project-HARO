from enum import Enum

class State (str, Enum):
    BOOT = "BOOT"
    IDLE = "IDLE"
    AWAKE = "AWAKE"
    LISTEN = "LISTEN"
    THINKING = "THINKING"
    TALK = "TALK"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"

# Para cada estado, para onde eles podem ir

TRANSITIONS: dict[State, set[State]] = {
    State.BOOT:     {State.IDLE},
    State.IDLE:     {State.AWAKE, State.LISTEN, State.THINKING, State.OFFLINE},
    State.AWAKE:    {State.LISTEN, State.IDLE, State.THINKING},
    State.LISTEN:   {State.THINKING, State.AWAKE, State.IDLE},
    State.THINKING: {State.TALK, State.ERROR, State.OFFLINE},
    State.TALK:     {State.AWAKE, State.IDLE},
    State.ERROR:    {State.IDLE, State.OFFLINE},
    State.OFFLINE:  {State.IDLE},
}

# Estado -> expressão (o corpo decide como desenhar)
EXPRESSION_MAP: dict[State, str] = {
    State.BOOT: "BOOT",
    State.IDLE: "IDLE",
    State.AWAKE: "ATTENTIVE",
    State.LISTEN: "LISTENING",
    State.THINKING: "THINKING",
    State.TALK: "TALKING",
    State.ERROR: "ERROR",
    State.OFFLINE: "OFFLINE",
}

# Estado -> comportamento do anel luminoso
RING_MAP: dict[State, str] = {
    State.BOOT: "blue_steady",
    State.IDLE: "dim_idle",
    State.AWAKE: "blue_steady",
    State.LISTEN: "cyan_pulse",
    State.THINKING: "purple_thinking",
    State.TALK: "green_ok",
    State.ERROR: "red_error",
    State.OFFLINE: "red_slow_pulse",
}

def can_transition(current:State, new: State) -> bool:
    return new in TRANSITIONS[current]