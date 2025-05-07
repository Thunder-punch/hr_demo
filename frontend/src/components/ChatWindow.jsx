// ChatWindow.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";

function ChatWindow({ messages, loading, onSendEmail }) {
  const containerRef = useRef(null);

  // 자동 스크롤 기능: 메시지가 추가될 때마다 스크롤을 맨 아래로 이동
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  const loadingMessages = useMemo(
    () => [
      "열일하는 중....",
      "서류 괜히 뒤져 보는 중....",
      "답변 준비하는 중....",
      "옆 부서에 물어보는 중...."
    ],
    []
  );
  const [loadingIndex, setLoadingIndex] = useState(0);

  useEffect(() => {
    if (!loading) {
      setLoadingIndex(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingIndex(prev => (prev + 1) % loadingMessages.length);
    }, 2000);
    return () => clearInterval(interval);
  }, [loading, loadingMessages.length]);

  useEffect(() => {
    console.log("[📦 메시지 상태]", messages);
  }, [messages]);

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, idx) => (
        <div key={idx}>
          {/* 본문 표시 */}
          <div
            className={`p-3 rounded-lg max-w-lg ${
              msg.isAI ? "bg-white shadow" : "bg-blue-100 ml-auto shadow-sm"
            }`}
          >
            <div className="whitespace-pre-wrap text-sm">{msg.text}</div>

            {/* ▼▼▼ 다운로드/이메일 버튼 표시 로직 추가 ▼▼▼ */}
            {msg.download_url && (
              <div className="mt-2 space-x-2">
                <a
                  href={msg.download_url}
                  className="text-blue-600 underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  📄 PDF 다운로드
                </a>
                <button
                  onClick={() => onSendEmail(msg.download_url)}
                  className="text-green-600 underline cursor-pointer"
                >
                  📩 PDF 이메일 발송
                </button>
              </div>
            )}
            {/* ▲▲▲ */}
          </div>

          {/* 테이블 표시 */}
          {msg.tableData && Array.isArray(msg.tableData) && msg.tableData.length > 0 && (
            <div className="overflow-x-auto mt-2">
              <table className="table-auto border-collapse border border-gray-300 text-sm">
                <thead>
                  <tr>
                    {Object.keys(msg.tableData[0]).map((key) => (
                      <th
                        key={key}
                        className="border border-gray-300 px-2 py-1 bg-gray-200"
                      >
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {msg.tableData.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {Object.values(row).map((cell, cellIndex) => (
                        <td
                          key={cellIndex}
                          className="border border-gray-300 px-2 py-1"
                        >
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}

      {/* 로딩 문구 */}
      {loading && (
        <div className="p-3 rounded-lg max-w-lg bg-white shadow text-gray-500 italic">
          {loadingMessages[loadingIndex]}
        </div>
      )}
    </div>
  );
}

export default ChatWindow;
