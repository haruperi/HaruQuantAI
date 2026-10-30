import { useState } from "react";
import { Sparkles, X } from "lucide-react";
export function AlgoWizardAI({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: () => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  return (
    <aside className="aw-ai-panel">
      <header>
        <Sparkles size={17} />
        <b>AI Wizard</b>
        <span className="aw-spacer" />
        <button aria-label="Close AI Wizard" onClick={onClose}>
          <X size={18} />
        </button>
      </header>
      <p className="aw-demo">Local AI demonstration · no messages are sent</p>
      <div className="aw-chat-history">
        {messages.length ? (
          messages.map((m, i) => (
            <div className="aw-chat-message" key={i}>
              <p>{m}</p>
              <p className="aw-muted">
                Demo response: try an EMA crossover strategy with long and short
                entry rules.
              </p>
              <button className="aw-primary" onClick={onCreate}>
                Open example strategy
              </button>
            </div>
          ))
        ) : (
          <div className="aw-chat-welcome">
            <h2>AI Strategy Wizard</h2>
            <p>Describe your strategy idea</p>
            <a
              href="https://strategyquant.com/blog/sq-ai-introduction"
              target="_blank"
              rel="noreferrer"
            >
              Quick introduction ↗
            </a>
            <a
              href="https://strategyquant.com/sq-ai-pricing"
              target="_blank"
              rel="noreferrer"
            >
              Plans and pricing ↗
            </a>
          </div>
        )}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (prompt.trim()) {
            setMessages([...messages, prompt.trim()]);
            setPrompt("");
          }
        }}
      >
        <textarea
          aria-label="Message AI Wizard"
          placeholder="Describe your strategy..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <button className="aw-primary" disabled={!prompt.trim()}>
          Send
        </button>
        <button type="button" onClick={() => setMessages([])}>
          New chat
        </button>
      </form>
    </aside>
  );
}
