const KNOWN_EXPRESSIONS = new Set([
  "BOOT",
  "IDLE",
  "ATTENTIVE",
  "LISTENING",
  "THINKING",
  "TALKING",
  "HAPPY",
  "CURIOUS",
  "CONFUSED",
  "ERROR",
  "OFFLINE",
]);
type Props = { expression: string; ring: string };
export function Face({ expression, ring }: Props) {
  // Expressão desconhecida? Cai em IDLE, que é seguro.
  const safe = KNOWN_EXPRESSIONS.has(expression) ? expression : "IDLE";
  return (
    <div className="haro" data-expression={safe} data-ring={ring}>
      <div className="ring" />
      <div className="body" />
      <div className="eye left" />
      <div className="eye right" />
      {/* Camada invisível por cima: é a alça de arraste da janela */}
      <div className="drag" data-tauri-drag-region />
    </div>
  );
}
