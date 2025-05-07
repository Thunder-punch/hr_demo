// 📁 src/pages/BossMainPage.jsx

import React, { useState } from "react";
import Header from "../components/Header";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";

function BossMainPage() {
  const [messages, setMessages] = useState([
    {
      text: "저는 AI기반ERP 인사과장A 입니다. 무엇을 도와드릴까요?",
      isAI: true,
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  const handleContractCreation = async () => {
    const contractData = {
      employee_name: prompt("근로자 이름을 입력해 주세요."),
      employee_address: prompt("회사명 또는 주소를 입력해 주세요."),
      position: prompt("직위를 입력해 주세요."),
      start_date: prompt("근로 시작일을 입력해 주세요 (YYYY-MM-DD)"),
      contract_period: prompt("근로 종료일이 있다면 입력해 주세요. 없다면 '생략'이라고 입력"),
      working_hours: prompt("근무 시간을 입력해 주세요 (예: 09:00~18:00)"),
      salary: parseInt(prompt("월 급여를 숫자로 입력해 주세요."), 10),
      additional_terms: prompt("추가 조건이 있다면 입력해 주세요. 없다면 '없음'이라고 입력"),
      email: prompt("계약서 파일을 받을 e-mail 주소를 입력해 주세요.")
    };

    try {
      const res = await fetch("http://localhost:8000/contract/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(contractData)
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { text: data.message, isAI: true },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { text: "계약서 생성에 실패했습니다.", isAI: true },
      ]);
    }
  };

  const handleQuickSubmit = async (text) => {
    if (!text?.trim()) return;
    const userMessage = { text, isAI: false };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/generate/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text }),
      });
      const data = await res.json();
      console.log("[응답 확인 - 사장 페이지]", data);

      const aiText =
        typeof data.generated_text === "object"
          ? JSON.stringify(data.generated_text, null, 2)
          : data.generated_text;

      const aiMessage = {
        text: aiText,
        isAI: true,
        tableData: data.table_data || [],
        download_url: data.download_url || null,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("❌ 서버 오류:", error);
      setMessages((prev) => [
        ...prev,
        { text: "서버와 통신할 수 없습니다.", isAI: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSendEmail = async (downloadUrl) => {
    const emailUrl = downloadUrl.replace("/pdf/", "/send-mail/");
    try {
      const res = await fetch(emailUrl);
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { text: data.message || "메일 전송 완료", isAI: true },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { text: "메일 발송에 실패했습니다.", isAI: true },
      ]);
    }
  };

  return (
    // pt-16: 고정 헤더의 높이(약 64px)를 고려한 여백
    <div className="min-h-screen bg-gray-50 flex flex-col relative pt-16">
      <Header />

      <div className="flex flex-1">
        {/* 왼쪽 사이드바: fixed로 설정하여 헤더(상단)와 푸터(하단) 사이에 고정 */}
        <div className="w-48 bg-yellow-100 p-4 shadow-inner fixed top-16 bottom-16">
          <div className="font-bold text-gray-700 mb-4">사장 메뉴</div>
          <button
            className="w-full py-2 mb-2 bg-white rounded shadow text-sm"
            onClick={handleContractCreation}
          >
            근로계약서
          </button>
          <button
            className="w-full py-2 mb-2 bg-white rounded shadow text-sm"
            onClick={() => handleQuickSubmit("전 직원 목록")}
          >
            전 직원 목록
          </button>
          <button
            className="w-full py-2 mb-2 bg-white rounded shadow text-sm"
            onClick={() => handleQuickSubmit("전 직원 급여명세서")}
          >
            전 직원 급여명세서
          </button>
          <button
            className="w-full py-2 mb-2 bg-white rounded shadow text-sm"
            onClick={() => handleQuickSubmit("정태우 현시간 출근")}
          >
            현시간 출근
          </button>
          <button
            className="w-full py-2 bg-white rounded shadow text-sm"
            onClick={() => handleQuickSubmit("정태우 현시간 퇴근")}
          >
            현시간 퇴근
          </button>
        </div>
        {/* 오른쪽 채팅 영역: 왼쪽 사이드바 너비(48)를 고려한 ml-48 */}
        <div className="flex flex-col flex-1 ml-48">
          <div className="flex-1 overflow-y-auto p-4">
            <ChatWindow messages={messages} loading={loading} onSendEmail={handleSendEmail} />
          </div>
          <div className="p-4 border-t bg-white">
            <ChatInput
              question={question}
              setQuestion={setQuestion}
              handleSubmit={(q) => handleQuickSubmit(q)}
              loading={loading}
            />
          </div>
        </div>
      </div>

      <footer className="text-center text-xs text-gray-400 p-2">
        인사과장A는 참고용으로만 사용해 주세요. 중요한 사항은 HR 담당자에게 문의하세요.
      </footer>
    </div>
  );
}

export default BossMainPage;
