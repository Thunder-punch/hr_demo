import React, { useState } from 'react';
import Header from '../components/Header';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';

function SalaryPage() {
  const [messages, setMessages] = useState([
    { text: "안녕하세요. 궁금한 급여 내용을 질문해보세요!", isAI: true }
  ]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!question.trim()) return;
    await handleSend(question);
    setQuestion('');
  };

  const handleSend = async (text) => {
    const userMessage = { text, isAI: false };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/generate/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text }),
      });

      const data = await res.json();
      console.log("[응답 확인 - 급여 페이지]", data);

      const aiMessage = {
        text: data.generated_text,
        isAI: true,
        tableData: data.table_data || [],
        download_url: data.download_url || null
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error("❌ 급여 페이지 서버 오류:", err);
      setMessages(prev => [...prev, { text: "서버 통신 실패", isAI: true }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      <div className="flex flex-1">
        <div className="flex flex-col flex-1">
          <ChatWindow messages={messages} loading={loading} />

          <div className="p-4 border-t bg-white">
            <ChatInput
              question={question}
              setQuestion={setQuestion}
              handleSubmit={handleSubmit}
              loading={loading}
            />
          </div>
        </div>
      </div>

      <footer className="text-center text-xs text-gray-400 p-2">
        궁금한 급여는 AI에게 물어보세요. 정확한 정보는 HR 담당자에게 문의하세요.
      </footer>
    </div>
  );
}

export default SalaryPage;
