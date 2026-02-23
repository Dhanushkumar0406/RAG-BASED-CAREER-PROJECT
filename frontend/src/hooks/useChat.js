import { useEffect, useState } from "react";
import { chat, health } from "../services/api";

export const useChat = () => {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi! Ask me about the jobs data and I'll answer using retrieved context." },
  ]);
  const [status, setStatus] = useState("checking");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    health()
      .then(() => setStatus("online"))
      .catch(() => setStatus("offline"));
  }, []);

  const sendMessage = async (question) => {
    const trimmed = question.trim();
    if (!trimmed) return;
    const userMsg = { role: "user", text: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const data = await chat(trimmed);
      const answer = data?.answer || "No response.";
      setMessages((prev) => [...prev, { role: "assistant", text: answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Error contacting backend. Check server/API key." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return { messages, status, loading, sendMessage };
};

export default useChat;
