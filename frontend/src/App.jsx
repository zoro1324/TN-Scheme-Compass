import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import ChatBubble from "./components/ChatBubble";
import SchemeCard from "./components/SchemeCard";
import SplineHero from "./components/SplineHero";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const uiText = {
  en: {
    hero: {
      kicker: "TN Scheme Compass",
      title: "AI Welfare Scheme Assistant",
      subtitle: "Ask naturally. Get clear eligibility, benefits, and application guidance in one place.",
    },
    welcome:
      "Tell me your situation, and I will find Tamil Nadu schemes with full eligibility, benefits, documents, and application details.",
    composerPlaceholder:
      "Example: I am a 32 year old woman, OBC, earning 2.4 lakh yearly. Which schemes can I apply for?",
    quickActions: ["Check eligibility", "List schemes", "Required documents"],
    conversation: "Conversation",
    assistantThinking: "Assistant is thinking...",
    send: "Send",
    session: {
      issue: "Session issue",
      connected: "Connected",
      starting: "Starting",
    },
    languageLabel: "Language",
    startVoiceInput: "Start voice input",
    stopVoiceInput: "Stop voice input",
    voiceRepliesOn: "Voice replies on",
    voiceRepliesOff: "Voice replies off",
    listening: "Listening...",
    voiceUnsupported: "Voice input not supported in this browser.",
    voiceNoSpeech: "No voice detected. Please try again.",
    voiceBlocked: "Microphone access is blocked. Allow mic permission to use voice chat.",
    voiceInputFailed: "Voice input failed. Please try again.",
    voiceStartFailed: "Unable to start microphone. Please try again.",
    ttsUnsupported: "Text-to-speech is not supported in this browser.",
    sessionInitFailed: "Session init failed",
    errorPrefix: "Error",
    schemeLabels: {
      benefit: "Benefit",
      amount: "Amount",
      eligibility: "Eligibility",
      documents: "Documents",
      apply: "Apply",
      openApplication: "Open Application Link",
      na: "N/A",
    },
  },
  ta: {
    hero: {
      kicker: "TN Scheme Compass",
      title: "AI நலத்திட்ட உதவியாளர்",
      subtitle: "இயல்பாக கேளுங்கள். தகுதி, நன்மைகள், மற்றும் விண்ணப்ப வழிகாட்டுதலை தெளிவாக பெறுங்கள்.",
    },
    welcome:
      "உங்கள் நிலையை பகிருங்கள்; தகுதி, நன்மைகள், ஆவணங்கள் மற்றும் விண்ணப்ப விவரங்களுடன் பொருந்தும் தமிழ்நாடு திட்டங்களை நான் கண்டுபிடித்து தருகிறேன்.",
    composerPlaceholder:
      "உதாரணம்: நான் 32 வயது பெண், OBC, ஆண்டு வருமானம் 2.4 லட்சம். எனக்கு எந்த திட்டங்கள் பொருந்தும்?",
    quickActions: ["தகுதி சரிபார்", "திட்டங்களை பட்டியலிடு", "தேவையான ஆவணங்கள்"],
    conversation: "உரையாடல்",
    assistantThinking: "உதவியாளர் யோசித்து கொண்டிருக்கிறார்...",
    send: "அனுப்பு",
    session: {
      issue: "அமர்வு சிக்கல்",
      connected: "இணைந்துள்ளது",
      starting: "தொடங்குகிறது",
    },
    languageLabel: "மொழி",
    startVoiceInput: "குரல் உள்ளீட்டை தொடங்கு",
    stopVoiceInput: "குரல் உள்ளீட்டை நிறுத்து",
    voiceRepliesOn: "குரல் பதில் செயல்பாட்டில்",
    voiceRepliesOff: "குரல் பதில் செயலற்றது",
    listening: "கேட்டுக்கொண்டிருக்கிறது...",
    voiceUnsupported: "இந்த உலாவியில் குரல் உள்ளீடு ஆதரிக்கப்படவில்லை.",
    voiceNoSpeech: "குரல் கண்டறியப்படவில்லை. மீண்டும் முயற்சிக்கவும்.",
    voiceBlocked: "மைக்ரோஃபோன் அணுகல் தடுக்கப்பட்டுள்ளது. அனுமதி அளிக்கவும்.",
    voiceInputFailed: "குரல் உள்ளீடு தோல்வியடைந்தது. மீண்டும் முயற்சிக்கவும்.",
    voiceStartFailed: "மைக்ரோஃபோனை தொடங்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.",
    ttsUnsupported: "இந்த உலாவியில் உரையை குரலாக்கும் வசதி இல்லை.",
    sessionInitFailed: "அமர்வு தொடக்கம் தோல்வி",
    errorPrefix: "பிழை",
    schemeLabels: {
      benefit: "நன்மை",
      amount: "தொகை",
      eligibility: "தகுதி",
      documents: "ஆவணங்கள்",
      apply: "விண்ணப்பம்",
      openApplication: "விண்ணப்ப இணைப்பை திற",
      na: "தகவல் இல்லை",
    },
  },
};

const normalizeLanguage = (value) => (value === "ta" ? "ta" : "en");

const getInitialLanguage = () => {
  if (typeof window === "undefined") return "en";
  return normalizeLanguage(window.localStorage.getItem("tn_language"));
};

const createMessage = (role, text, schemes = [], variant = "default") => ({
  id: crypto.randomUUID(),
  role,
  text,
  schemes,
  variant,
});

export default function App() {
  const [uiLanguage, setUiLanguage] = useState(getInitialLanguage);
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
      uiText[getInitialLanguage()].welcome,
    ),
  ]);
  const copy = uiText[uiLanguage];
  const listEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const draftRef = useRef("");

  useEffect(() => {
    draftRef.current = draft;
  }, [draft]);

  useEffect(() => {
    window.localStorage.setItem("tn_language", uiLanguage);
  }, [uiLanguage]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceSupported(false);
      return;
    }

    setVoiceSupported(true);
    const recognition = new SpeechRecognition();
    recognition.lang = uiLanguage === "ta" ? "ta-IN" : "en-IN";
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
        setVoiceError(uiText[uiLanguage].voiceNoSpeech);
      } else if (event.error === "not-allowed") {
        setVoiceError(uiText[uiLanguage].voiceBlocked);
      } else {
        setVoiceError(uiText[uiLanguage].voiceInputFailed);
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
  }, [uiLanguage]);

  useEffect(() => {
    const boot = async () => {
      const response = await axios.post(`${API_BASE}/api/chat/session`);
      setSessionId(response.data.session_id);
    };

    boot().catch((err) => {
      setSessionError(true);
      setMessages((prev) => [
        ...prev,
        createMessage("assistant", `${uiText[getInitialLanguage()].sessionInitFailed}: ${err.message}`, [], "warning"),
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
    utterance.lang = uiLanguage === "ta" ? "ta-IN" : "en-IN";
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }, [messages, autoSpeak, uiLanguage]);

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
        language: uiLanguage,
      });

      const payload = response.data;

      setMessages((prev) => {
        return [...prev, createMessage("assistant", payload.reply, payload.schemes || [])];
      });
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message;
      setMessages((prev) => [...prev, createMessage("assistant", `${copy.errorPrefix}: ${detail}`, [], "warning")]);
    } finally {
      setLoading(false);
    }
  };

  const sessionStatus = sessionError
    ? { text: copy.session.issue, tone: "warning" }
    : sessionId
      ? { text: copy.session.connected, tone: "ok" }
      : { text: copy.session.starting, tone: "pending" };

  const handleQuickAction = (action) => {
    setDraft((prev) => {
      if (!prev.trim()) return action;
      return `${prev.trim()} ${action}`;
    });
  };

  const toggleListening = () => {
    if (!voiceSupported || !recognitionRef.current) {
      setVoiceError(copy.voiceUnsupported);
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
      setVoiceError(copy.voiceStartFailed);
      setIsListening(false);
    }
  };

  const toggleAutoSpeak = () => {
    if (!window.speechSynthesis) {
      setVoiceError(copy.ttsUnsupported);
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
        <SplineHero text={copy.hero} />

        <main className="chat-shell">
          <div className="chat-header">
            <p className="chat-header__title">{copy.conversation}</p>
            <div className="chat-header__controls">
              <div className="language-switch" role="group" aria-label={copy.languageLabel}>
                <button
                  type="button"
                  className={`language-switch__button ${uiLanguage === "en" ? "language-switch__button--active" : ""}`}
                  onClick={() => setUiLanguage("en")}
                >
                  EN
                </button>
                <button
                  type="button"
                  className={`language-switch__button ${uiLanguage === "ta" ? "language-switch__button--active" : ""}`}
                  onClick={() => setUiLanguage("ta")}
                >
                  தமிழ்
                </button>
              </div>
              <span className={`session-indicator session-indicator--${sessionStatus.tone}`}>
                <span className="session-indicator__dot" aria-hidden="true" />
                {sessionStatus.text}
              </span>
            </div>
          </div>

          <div className="chat-scroll">
            {messages.map((msg) => (
              <ChatBubble key={msg.id} role={msg.role} text={msg.text} variant={msg.variant}>
                {msg.schemes?.length ? (
                  <div className="inline-scheme-stack">
                    {msg.schemes.map((scheme) => (
                      <SchemeCard key={scheme.scheme_id} scheme={scheme} labels={copy.schemeLabels} />
                    ))}
                  </div>
                ) : null}
              </ChatBubble>
            ))}
            {loading && (
              <div className="chat-thinking" role="status" aria-live="polite">
                {copy.assistantThinking}
              </div>
            )}
            <div ref={listEndRef} />
          </div>

          <form onSubmit={sendMessage} className="composer">
            <div className="composer__bar">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={copy.composerPlaceholder}
                className="composer__input"
              />
              <button
                type="button"
                className={`composer__voice ${isListening ? "composer__voice--active" : ""}`}
                onClick={toggleListening}
                aria-label={isListening ? copy.stopVoiceInput : copy.startVoiceInput}
                title={isListening ? copy.stopVoiceInput : copy.startVoiceInput}
              >
                🎙
              </button>
              <button
                type="submit"
                disabled={!canSend}
                className="composer__send"
                aria-label={copy.send}
              >
                <span aria-hidden="true">➤</span>
                <span className="composer__send-label">{copy.send}</span>
              </button>
            </div>
            <div className="voice-controls" aria-live="polite">
              <button
                type="button"
                className={`voice-controls__toggle ${autoSpeak ? "voice-controls__toggle--on" : ""}`}
                onClick={toggleAutoSpeak}
              >
                {autoSpeak ? copy.voiceRepliesOn : copy.voiceRepliesOff}
              </button>
              {isListening && <span className="voice-controls__status">{copy.listening}</span>}
              {!voiceSupported && <span className="voice-controls__status voice-controls__status--warning">{copy.voiceUnsupported}</span>}
              {voiceError && <span className="voice-controls__status voice-controls__status--warning">{voiceError}</span>}
            </div>
            <div className="quick-actions" aria-label="Quick actions">
              {copy.quickActions.map((action) => (
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
