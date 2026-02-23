import Navbar from "../components/Navbar";
import ChatBox from "../components/ChatBox";

const Home = () => {
  return (
    <div className="app-shell">
      <Navbar />
      <header className="app-header">
        <h1>Career RAG Assistant</h1>
        <p className="subtitle">Ask questions about the scraped job data with context-aware answers.</p>
      </header>
      <main className="app-main">
        <ChatBox />
      </main>
    </div>
  );
};

export default Home;
