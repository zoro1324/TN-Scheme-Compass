import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import ChatBubble from "./components/ChatBubble";
import SchemeCard from "./components/SchemeCard";
import SplineHero from "./components/SplineHero";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const composerPlaceholder =
  "Example: I am a 32 year old woman, OBC, earning 2.4 lakh yearly. Which schemes can I apply for?";

const quickActions = [
  "Check eligibility",
  "List schemes",
  "Required documents",
];

const createMessage = (role, text, schemes = [], variant = "default") => ({
  id: crypto.randomUUID(),
  role,
  text,
  schemes,
  variant,
});

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [sessionError, setSessionError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState([
    createMessage(
      "assistant",
      "Tell me your situation, and I will find Tamil Nadu schemes with full eligibility, benefits, documents, and application details.",
    ),
  ]);
  const listEndRef = useRef(null);

  useEffect(() => {
    const boot = async () => {
      const response = await axios.post(`${API_BASE}/api/chat/session`);
      setSessionId(response.data.session_id);
    };

    boot().catch((err) => {
      setSessionError(true);
      setMessages((prev) => [
        ...prev,
        createMessage("assistant", `Session init failed: ${err.message}`, [], "warning"),
      ]);
    });
  }, []);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const canSend = useMemo(() => Boolean(draft.trim()) && Boolean(sessionId) && !loading, [draft, sessionId, loading]);

  const sendMessage = async (event) => {
    event.preventDefault();
    if (!canSend) return;

    const text = draft.trim();
    setDraft("");
    setLoading(true);
    setMessages((prev) => [...prev, createMessage("user", text)]);

    try {
      const response = await axios.post(`${API_BASE}/api/chat/message`, {
        session_id: sessionId,
        message: text,
      });

      const payload = response.data;

      setMessages((prev) => {
        const next = [...prev, createMessage("assistant", payload.reply, payload.schemes || [])];
        if (payload.follow_up_question) {
          next.push(createMessage("assistant", `Next question: ${payload.follow_up_question}`));
        }
        return next;
      });
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message;
      setMessages((prev) => [...prev, createMessage("assistant", `Error: ${detail}`, [], "warning")]);
    } finally {
      setLoading(false);
    }
  };

  const sessionStatus = sessionError
    ? { text: "Session issue", tone: "warning" }
    : sessionId
      ? { text: "Connected", tone: "ok" }
      : { text: "Starting", tone: "pending" };

  const handleQuickAction = (action) => {
    setDraft((prev) => {
      if (!prev.trim()) return action;
      return `${prev.trim()} ${action.toLowerCase()}`;
    });
  };

  return (
    <div className="app-shell">
      <div className="app-inner">
        <SplineHero />

        <main className="chat-shell">
          <div className="chat-header">
            <p className="chat-header__title">Conversation</p>
            <span className={`session-indicator session-indicator--${sessionStatus.tone}`}>
              <span className="session-indicator__dot" aria-hidden="true" />
              {sessionStatus.text}
            </span>
          </div>

          <div className="chat-scroll">
            {messages.map((msg) => (
              <ChatBubble key={msg.id} role={msg.role} text={msg.text} variant={msg.variant}>
                {msg.schemes?.length ? (
                  <div className="inline-scheme-stack">
                    {msg.schemes.map((scheme) => (
                      <SchemeCard key={scheme.scheme_id} scheme={scheme} />
                    ))}
                  </div>
                ) : null}
              </ChatBubble>
            ))}
            {loading && (
              <div className="chat-thinking" role="status" aria-live="polite">
                Assistant is thinking...
              </div>
            )}
            <div ref={listEndRef} />
          </div>

          <form onSubmit={sendMessage} className="composer">
            <div className="composer__bar">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={composerPlaceholder}
                className="composer__input"
              />
              <button
                type="submit"
                disabled={!canSend}
                className="composer__send"
                aria-label="Send message"
              >
                <span aria-hidden="true">➤</span>
                <span className="composer__send-label">Send</span>
              </button>
            </div>
            <div className="quick-actions" aria-label="Quick actions">
              {quickActions.map((action) => (
                <button
                  key={action}
                  type="button"
                  className="quick-actions__chip"
                  onClick={() => handleQuickAction(action)}
                >
                  {action}
                </button>
              ))}
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}
