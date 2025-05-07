import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../logo.png';

function SignupPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    position: '사원',
    phone: '',
    startDate: '',
    base_salary: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const res = await fetch("http://localhost:8000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: formData.username,
          email: formData.email,
          password: formData.password,
          phone: formData.phone,
          position: formData.position,
          startDate: formData.startDate,
          base_salary: parseInt(formData.base_salary, 10)
        })
      });

      if (!res.ok) {
        const result = await res.json();
        throw new Error(result.detail || "회원가입 실패");
      }

      const welcomeMessage = "회원가입을 환영합니다.";
      const path = formData.position === '사장' ? '/boss' : '/employee';
      navigate(path, {
        state: { welcomeMessage },
      });

    } catch (err) {
      alert("회원가입 실패: " + err.message);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 px-4">
      <div className="flex flex-col items-center bg-white p-8 rounded-xl shadow-md w-full max-w-sm space-y-5">
        <img src={logo} alt="하엘프랜즈 로고" className="h-12 mb-1" />
        <h2 className="text-2xl font-semibold text-gray-800">회원가입</h2>

        <form onSubmit={handleSubmit} className="w-full space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">이름</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="이름 입력"
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">이메일</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="이메일 입력"
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">비밀번호</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="비밀번호 입력"
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">직책</label>
            <select
              name="position"
              value={formData.position}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
            >
              <option value="사원">사원</option>
              <option value="사장">사장</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">전화번호</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="010-0000-0000"
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">입사일</label>
            <input
              type="date"
              name="startDate"
              value={formData.startDate}
              onChange={handleChange}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">기본급</label>
            <input
              type="number"
              name="base_salary"
              value={formData.base_salary}
              onChange={handleChange}
              placeholder="예: 3000000"
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          >
            가입하기
          </button>
        </form>
      </div>
    </div>
  );
}

export default SignupPage;
