import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../services/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  if (!user) return null;
  const isStudent = user.role === "student";
  return (
    <nav className="nav">
      <strong>Assignment Portal</strong>
      {isStudent ? (
        <>
          <Link to="/student">Dashboard</Link>
          <Link to="/student/assignments">Assignments</Link>
          <Link to="/student/submissions">My Submissions</Link>
        </>
      ) : (
        <>
          <Link to="/teacher">Dashboard</Link>
          <Link to="/teacher/assignments">Assignments</Link>
        </>
      )}
      <span className="spacer" />
      <span>{user.name} ({user.role})</span>
      <button onClick={async () => { await logout(); nav("/login"); }}>Logout</button>
    </nav>
  );
}
