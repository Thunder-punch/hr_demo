import React, { useState } from "react";

function CheckinPage() {
  const [userId, setUserId] = useState("");
  const [response, setResponse] = useState("");

  const handleCheckin = async () => {
    if (!userId) {
      setResponse("❗ user_id를 입력해주세요.");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/attendance/check-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: parseInt(userId) }),
      });

      const data = await res.json();
      if (res.ok) {
        setResponse(`✅ 출근 완료! (${data.time})`);
      } else {
        setResponse(`❌ ${data.detail}`);
      }
    } catch (error) {
      setResponse("🚨 서버 연결 실패");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4 bg-gray-50">
      <h1 className="text-2xl font-bold">인사과장A 출근 시스템</h1>

      <input
        type="number"
        placeholder="user_id 입력"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        className="border rounded px-4 py-2 w-64"
      />

      <button
        onClick={handleCheckin}
        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded"
      >
        출근하기
      </button>

      {response && <div className="mt-4 text-sm text-gray-700">{response}</div>}
    </div>
  );
}

export default CheckinPage;
