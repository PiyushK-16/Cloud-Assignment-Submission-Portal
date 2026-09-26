import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./services/AuthContext";
import Login from "./pages/Login";
import Register from "./pages/Register";
import StudentDashboard from "./pages/StudentDashboard";
import StudentAssignments from "./pages/StudentAssignments";
import MySubmissions from "./pages/MySubmissions";
import TeacherDashboard from "./pages/TeacherDashboard";
import TeacherAssignments from "./pages/TeacherAssignments";
import TeacherSubmissions from "./pages/TeacherSubmissions";

export default function App() {
  const { user } = useAuth();
  const home = user ? (user.role === "student" ? "/student" : "/teacher") : "/login";
  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<Navigate to={home} replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/student" element={<ProtectedRoute role="student"><StudentDashboard /></ProtectedRoute>} />
          <Route path="/student/assignments" element={<ProtectedRoute role="student"><StudentAssignments /></ProtectedRoute>} />
          <Route path="/student/submissions" element={<ProtectedRoute role="student"><MySubmissions /></ProtectedRoute>} />
          <Route path="/teacher" element={<ProtectedRoute role="teacher"><TeacherDashboard /></ProtectedRoute>} />
          <Route path="/teacher/assignments" element={<ProtectedRoute role="teacher"><TeacherAssignments /></ProtectedRoute>} />
          <Route path="/teacher/assignments/:id" element={<ProtectedRoute role="teacher"><TeacherSubmissions /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to={home} replace />} />
        </Routes>
      </main>
    </>
  );
}
