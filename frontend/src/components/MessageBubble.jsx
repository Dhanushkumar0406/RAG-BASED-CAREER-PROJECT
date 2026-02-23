import PropTypes from "prop-types";

const MessageBubble = ({ role, text, timestamp }) => {
  const isUser = role === "user";
  return (
    <div className={`bubble-row ${isUser ? "align-end" : "align-start"}`}>
      <div className={`bubble ${isUser ? "user" : "assistant"}`}>
        <div className="bubble-text">{text}</div>
        {timestamp && <div className="bubble-meta">{timestamp}</div>}
      </div>
    </div>
  );
};

MessageBubble.propTypes = {
  role: PropTypes.oneOf(["user", "assistant"]).isRequired,
  text: PropTypes.string.isRequired,
  timestamp: PropTypes.string,
};

export default MessageBubble;
