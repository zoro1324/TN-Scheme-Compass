export default function ChatBubble({ role, text }) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm md:max-w-[75%] ${
          isUser
            ? "bg-brand-600 text-white"
            : "glow-panel border border-white/70 text-slate-800"
        }`}
      >
        {text}
      </div>
    </div>
  );
}
