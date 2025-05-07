// 📁 src/App.jsx

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";  // 회원가입 페이지
import EmployeeMainPage from "./pages/EmployeeMainPage";
import BossMainPage from "./pages/BossMainPage";
import SalaryPage from "./pages/SalaryPage";  // 급여 조회 페이지

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/employee" element={<EmployeeMainPage />} />
        <Route path="/boss" element={<BossMainPage />} />
        <Route path="/salary" element={<SalaryPage />} />
      </Routes>
    </Router>
  );
}

export default App;
