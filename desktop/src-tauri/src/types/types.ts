export type StateChangeEvent = {
  type: "state_change";
  state: string;
  expression: string;
  ring: string;
};

export type TranscriptEvent = {
  type: "transcript";
  text: string;
  emotion: string | null;
};

export type HaroEvent = StateChangeEvent | TranscriptEvent;
