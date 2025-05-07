// 📄 src/components/ChatInput.jsx
import React from "react";

function ChatInput({ question, setQuestion, handleSubmit, loading }) {
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSubmit(question);
      setQuestion(""); // 전송 후 입력 필드 초기화
    }
  };

  return (
    <div className="flex">
      <input
        type="text"
        className="flex-1 px-4 py-2 rounded-l-lg border border-gray-300"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="메시지 입력"
        onKeyDown={handleKeyDown}
        disabled={loading}
      />
      <button
        className="px-4 py-2 bg-blue-500 text-white rounded-r-lg hover:bg-blue-600"
        onClick={() => {
          handleSubmit(question);
          setQuestion("");
        }}
        disabled={loading}
      >
        전송
      </button>
    </div>
  );
}

export default ChatInput;
