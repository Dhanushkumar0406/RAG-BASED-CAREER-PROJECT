import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import Loader from "./Loader";
import useChat from "../hooks/useChat";

const ChatBox = () => {
  const { messages, status, loading, sendMessage } = useChat();
  const [input, setInput] = useState("");
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSend = () => {
    if (loading) return;
    sendMessage(input);
    setInput("");
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chatbox">
      <div className="chat-status">
        <span className={`status-dot ${status === "online" ? "ok" : "warn"}`} />
        {status === "online" ? "Backend online" : "Backend offline"}
      </div>
      <div className="chat-history" ref={listRef}>
        {messages.map((m, idx) => (
          <MessageBubble key={idx} role={m.role} text={m.text} />
        ))}
        {loading && <Loader />}
      </div>
      <div className="chat-input">
        <textarea
          placeholder="Type your question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          rows={2}
        />
        <button onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatBox;
