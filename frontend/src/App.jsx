import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import ChatBubble from "./components/ChatBubble";
import SchemeCard from "./components/SchemeCard";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Tell me your situation, and I will find Tamil Nadu schemes with full eligibility, benefits, documents, and application details.",
    },
  ]);
  const [schemeCards, setSchemeCards] = useState([]);
  const listEndRef = useRef(null);

  useEffect(() => {
    const boot = async () => {
      const response = await axios.post(`${API_BASE}/api/chat/session`);
      setSessionId(response.data.session_id);
    };

    boot().catch((err) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Session init failed: ${err.message}` },
      ]);
    });
  }, []);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, schemeCards]);

  const canSend = useMemo(() => Boolean(draft.trim()) && Boolean(sessionId) && !loading, [draft, sessionId, loading]);

  const sendMessage = async (event) => {
    event.preventDefault();
    if (!canSend) return;

    const text = draft.trim();
    setDraft("");
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", text }]);

    try {
      const response = await axios.post(`${API_BASE}/api/chat/message`, {
        session_id: sessionId,
        message: text,
      });

      const payload = response.data;

      setMessages((prev) => {
        const next = [...prev, { role: "assistant", text: payload.reply }];
        if (payload.follow_up_question) {
          next.push({ role: "assistant", text: `Next question: ${payload.follow_up_question}` });
        }
        return next;
      });

      setSchemeCards(payload.schemes || []);
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message;
      setMessages((prev) => [...prev, { role: "assistant", text: `Error: ${detail}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-6 md:px-6 md:py-8">
      <header className="mb-5 rounded-3xl bg-ink px-6 py-6 text-white shadow-lift">
        <p className="text-xs uppercase tracking-[0.16em] text-brand-200">TN Scheme Compass</p>
        <h1 className="font-heading text-2xl font-bold md:text-4xl">Dynamic Welfare Scheme Assistant</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-200 md:text-base">
          Ask in plain language. The assistant adapts questions to your inputs and returns complete scheme details, not generic replies.
        </p>
      </header>

      <main className="grid flex-1 gap-5 md:grid-cols-5">
        <section className="glow-panel md:col-span-3 flex min-h-[55vh] flex-col rounded-3xl border border-white/80 p-4 shadow-sm md:p-5">
          <div className="mb-3 text-xs font-medium text-slate-500">Session: {sessionId || "Starting..."}</div>
          <div className="flex-1 space-y-3 overflow-y-auto pr-1">
            {messages.map((msg, idx) => (
              <ChatBubble key={`${msg.role}-${idx}`} role={msg.role} text={msg.text} />
            ))}
            <div ref={listEndRef} />
          </div>

          <form onSubmit={sendMessage} className="mt-4 flex gap-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Example: I am a 32 year old woman, OBC, earning 2.4 lakh yearly. Which schemes can I apply for?"
              className="h-24 flex-1 resize-none rounded-2xl border border-brand-200 bg-white px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            />
            <button
              type="submit"
              disabled={!canSend}
              className="rounded-2xl bg-brand-600 px-5 py-3 font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {loading ? "Thinking..." : "Send"}
            </button>
          </form>
        </section>

        <aside className="md:col-span-2 rounded-3xl border border-white/80 bg-white/85 p-4 shadow-sm md:p-5">
          <h2 className="font-heading text-lg font-semibold text-ink">Matched Scheme Details</h2>
          <p className="mb-3 text-sm text-slate-600">Each card includes key details for eligibility and application.</p>
          <div className="space-y-3 overflow-y-auto md:max-h-[68vh]">
            {schemeCards.length ? (
              schemeCards.map((scheme) => <SchemeCard key={scheme.scheme_id} scheme={scheme} />)
            ) : (
              <p className="rounded-2xl bg-slate-50 p-3 text-sm text-slate-600">
                Scheme cards will appear here once you ask a question.
              </p>
            )}
          </div>
        </aside>
      </main>
    </div>
  );
}
