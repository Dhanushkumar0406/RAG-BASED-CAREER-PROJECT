import axios from "axios";

// Default to Flask's default port (5000). Override with VITE_API_BASE for other setups.
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";

export const chat = async (question, history = [], persona = "concise_career_coach") => {
  const resp = await axios.post(`${API_BASE}/chat`, { question, history, persona });
  return resp.data;
};

export const health = async () => {
  const resp = await axios.get(`${API_BASE}/health`);
  return resp.data;
};
