// 📁 src/pages/EmployeeMainPage.jsx
import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import Header from "../components/Header";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";

function EmployeeMainPage() {
  const location = useLocation();
  const userName = location.state?.userName; // 로그인 시 전달된 사용자 이름

  // 초기 메시지: 로그인 후 얼굴 인식이 자동 실행되었음을 안내
  const initialMessage = userName
    ? `안녕하세요, ${userName}님. 얼굴 인식을 시작합니다. 잠시만 기다려 주세요...`
    : "저는 AI 기반 ERP 인사과장A입니다. 무엇을 도와드릴까요?";

  const [messages, setMessages] = useState([{ text: initialMessage, isAI: true }]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  // 로그인 성공 후 자동 얼굴 인식 API 호출
  useEffect(() => {
    if (userName) {
      autoFaceLogin();
      const systemMsg = {
        text: `안녕하세요, ${userName}님. 얼굴 인식을 진행 중입니다.`,
        isAI: true,
      };
      setMessages([systemMsg]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userName]);

  // /face/login API를 호출하는 함수 (자동 얼굴 인식)
  async function autoFaceLogin() {
    try {
      const res = await fetch("http://localhost:8000/face/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // 예시로 비밀번호는 "1234"로 고정 (실제 서비스에서는 보안 강화 필요)
        body: JSON.stringify({ username: userName, password: "1234" }),
      });
      const data = await res.json();
      console.log("Face login response:", data);

      // 얼굴 인식 결과 메시지를 ChatWindow에 추가
      setMessages((prev) => [...prev, { text: data.message, isAI: true }]);
    } catch (error) {
      console.error("얼굴 인식 API 호출 오류:", error);
      setMessages((prev) => [...prev, { text: "얼굴 인식에 실패했습니다.", isAI: true }]);
    }
  }

  // onSendEmail 함수: PDF 이메일 발송 API 호출
  const handleSendEmail = async (downloadUrl) => {
    try {
      // 예시: 사용자 id가 1인 경우, /payroll/send-mail/1 엔드포인트 호출
      const res = await fetch("http://localhost:8000/payroll/send-mail/1", {
        method: "GET",
      });
      if (res.ok) {
        console.log("이메일 발송 성공");
      } else {
        console.error("이메일 발송 실패");
        alert("이메일 발송에 실패했습니다.");
      }
    } catch (error) {
      console.error("이메일 발송 에러:", error);
      alert("이메일 발송 중 오류 발생");
    }
  };

  // 기존의 질문 전송 함수
  const handleSubmit = async () => {
    if (!question.trim()) return;
    await handleQuickSubmit(question);
    setQuestion("");
  };

  // 질문 전송 및 AI 응답 처리 함수
  const handleQuickSubmit = async (text) => {
    const modifiedText = userName ? `${userName}의 ${text}` : text;
    console.log("Modified prompt:", modifiedText);
    const userMessage = { text: text, isAI: false };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/generate/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: modifiedText }),
      });
      const data = await res.json();
      console.log("[응답 확인]", data);

      const aiMessage = {
        text: data.generated_text,
        isAI: true,
        tableData: data.table_data || [],
        download_url: data.download_url || null,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("서버 오류:", error);
      setMessages((prev) => [
        ...prev,
        { text: "서버와 통신할 수 없습니다.", isAI: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col relative pt-16">
      <Header />
      <div className="flex flex-1">
        {/* 왼쪽 사이드바 */}
        <div className="w-48 bg-blue-100 p-4 shadow-inner fixed top-16 bottom-16">
          <div className="font-bold text-gray-700 mb-4">메뉴</div>
          <button
            className="w-full py-2 mb-2 bg-white rounded shadow text-sm"
            onClick={() => handleQuickSubmit("정태우 현시간 출근")}
          >
            출근
          </button>
          <button
            className="w-full py-2 mb-2 bg-white rounded shadow text-sm"
            onClick={() => handleQuickSubmit("정태우 현시간 퇴근")}
          >
            퇴근
          </button>
          <button
            className="w-full py-2 mb-2 bg-white rounded shadow text-sm"
            onClick={() => handleQuickSubmit("정태우 잔여 휴가 보여줘")}
          >
            잔여 휴가
          </button>
          <button
            className="w-full py-2 bg-white rounded shadow text-sm"
            onClick={() => handleQuickSubmit("정태우 급여명세서 보여줘")}
          >
            급여명세서
          </button>
        </div>
        {/* 오른쪽 채팅 영역 */}
        <div className="flex flex-col flex-1 ml-48">
          <div className="flex-1 overflow-y-auto p-4">
            <ChatWindow
              messages={messages}
              loading={loading}
              onSendEmail={handleSendEmail}
            />
          </div>
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
        인사과장A는 참고용으로만 사용해 주세요. 중요한 사항은 HR 담당자에게 문의하세요.
      </footer>
    </div>
  );
}

export default EmployeeMainPage;
