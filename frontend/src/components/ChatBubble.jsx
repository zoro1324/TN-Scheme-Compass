export default function ChatBubble({ role, text, children, variant = "default" }) {
  const isUser = role === "user";
  const isWarning = variant === "warning" && !isUser;
  const bubbleClassName = [
    "bubble",
    isUser ? "bubble--user" : "bubble--assistant",
    isWarning ? "bubble--warning" : "",
  ].filter(Boolean).join(" ");

  return (
    <div className={`bubble-row ${isUser ? "bubble-row--user" : "bubble-row--assistant"}`}>
      <article className={bubbleClassName}>
        <p className="bubble-text">{text}</p>
        {children}
      </article>
    </div>
  );
}
