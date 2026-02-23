import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:9000";

export const chat = async (question) => {
  const resp = await axios.post(`${API_BASE}/chat`, { question });
  return resp.data;
};

export const health = async () => {
  const resp = await axios.get(`${API_BASE}/health`);
  return resp.data;
};
