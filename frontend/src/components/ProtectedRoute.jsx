import { Navigate } from "react-router-dom";
import { useAuth } from "../services/AuthContext";

// Client-side guard (UX only). The REAL security is enforced by the backend on every request.
export default function ProtectedRoute({ role, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  const isTeacherSide = user.role === "teacher" || user.role === "admin";
  if (role === "student" && user.role !== "student") return <Navigate to="/teacher" replace />;
  if (role === "teacher" && !isTeacherSide) return <Navigate to="/student" replace />;
  return children;
}
