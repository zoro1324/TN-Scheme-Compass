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
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [messages, setMessages] = useState([
    createMessage(
      "assistant",
      "Tell me your situation, and I will find Tamil Nadu schemes with full eligibility, benefits, documents, and application details.",
    ),
  ]);
  const listEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const draftRef = useRef("");

  useEffect(() => {
    draftRef.current = draft;
  }, [draft]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceSupported(false);
      return;
    }

    setVoiceSupported(true);
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    recognition.onresult = (event) => {
      let finalTranscript = "";
      let interimTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const chunk = event.results[i][0]?.transcript || "";
        if (event.results[i].isFinal) {
          finalTranscript += `${chunk} `;
        } else {
          interimTranscript += `${chunk} `;
        }
      }

      const spokenText = (finalTranscript || interimTranscript).trim();
      if (!spokenText) return;

      setDraft(() => {
        const existing = draftRef.current.trim();
        return existing ? `${existing} ${spokenText}` : spokenText;
      });
    };

    recognition.onerror = (event) => {
      if (event.error === "no-speech") {
        setVoiceError("No voice detected. Please try again.");
      } else if (event.error === "not-allowed") {
        setVoiceError("Microphone access is blocked. Allow mic permission to use voice chat.");
      } else {
        setVoiceError("Voice input failed. Please try again.");
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
      window.speechSynthesis?.cancel();
    };
  }, []);

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

  useEffect(() => {
    if (!autoSpeak) return;
    if (!messages.length) return;

    const latest = messages[messages.length - 1];
    if (latest.role !== "assistant") return;
    if (latest.variant === "warning") return;
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(latest.text);
    utterance.lang = "en-IN";
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }, [messages, autoSpeak]);

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
        return [...prev, createMessage("assistant", payload.reply, payload.schemes || [])];
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

  const toggleListening = () => {
    if (!voiceSupported || !recognitionRef.current) {
      setVoiceError("Voice input is not supported in this browser.");
      return;
    }

    setVoiceError("");

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch {
      setVoiceError("Unable to start microphone. Please try again.");
      setIsListening(false);
    }
  };

  const toggleAutoSpeak = () => {
    if (!window.speechSynthesis) {
      setVoiceError("Text-to-speech is not supported in this browser.");
      return;
    }

    setVoiceError("");
    setAutoSpeak((prev) => {
      if (prev) {
        window.speechSynthesis.cancel();
      }
      return !prev;
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
                type="button"
                className={`composer__voice ${isListening ? "composer__voice--active" : ""}`}
                onClick={toggleListening}
                aria-label={isListening ? "Stop voice input" : "Start voice input"}
                title={isListening ? "Stop voice input" : "Start voice input"}
              >
                🎙
              </button>
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
            <div className="voice-controls" aria-live="polite">
              <button
                type="button"
                className={`voice-controls__toggle ${autoSpeak ? "voice-controls__toggle--on" : ""}`}
                onClick={toggleAutoSpeak}
              >
                {autoSpeak ? "Voice replies on" : "Voice replies off"}
              </button>
              {isListening && <span className="voice-controls__status">Listening...</span>}
              {!voiceSupported && <span className="voice-controls__status voice-controls__status--warning">Voice input not supported in this browser.</span>}
              {voiceError && <span className="voice-controls__status voice-controls__status--warning">{voiceError}</span>}
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
