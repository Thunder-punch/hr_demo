// 📁 src/pages/LoginPage.jsx

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import logo from "../logo.png";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: pw }),
      });

      const result = await res.json();

      if (res.ok) {
        console.log("로그인 응답 데이터:", result);

        if (result.position === "사장") {
          navigate("/boss");
        } else if (result.position === "사원") {
          navigate("/employee");
        } else {
          alert("역할 정보가 올바르지 않습니다.");
        }
      } else {
        let message =
          typeof result.detail === "string"
            ? result.detail
            : Array.isArray(result.detail) && result.detail[0]?.msg
            ? result.detail[0].msg
            : "로그인 실패";

        if (message.includes("value is not a valid email address")) {
          message = "이메일 형식으로 입력해 주세요.";
        }

        alert(message);
      }
    } catch (error) {
      console.error("로그인 요청 중 에러:", error);
      alert("서버와 연결할 수 없습니다. 다시 시도해주세요.");
    }
  };

  const handleRegister = () => {
    navigate("/signup");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="bg-white p-8 rounded shadow-md w-full max-w-sm space-y-6">
        <div className="flex justify-center mb-4">
          <img src={logo} alt="인사과장A 로고" className="h-12" />
        </div>
        <h2 className="text-2xl font-bold text-center text-gray-800">
        AI 기반 ERP 인사과장A
        <br />
        (데모버전)
      </h2>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">이메일</label>
          <input
            type="email"
            className="w-full border rounded px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="이메일 입력"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">비밀번호</label>
          <input
            type="password"
            className="w-full border rounded px-3 py-2"
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            placeholder="비밀번호 입력"
          />
        </div>

        <div className="flex flex-col gap-3">
          <button
            onClick={handleLogin}
            className="bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          >
            로그인
          </button>

          <button
            onClick={handleRegister}
            className="text-blue-600 border border-blue-600 py-2 rounded hover:bg-blue-50"
          >
            회원가입
          </button>
        </div>

        <p className="text-xs text-center text-gray-400 mt-2">
          데모버전은 회원가입 즉시 이용 가능하며, 비밀번호는 제한 없습니다.
        </p>
      </div>
    </div>
  );
}

export default LoginPage;