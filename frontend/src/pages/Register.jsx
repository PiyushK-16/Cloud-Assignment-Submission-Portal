import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function Register() {
  const nav = useNavigate();
  const [f, setF] = useState({ name: "", email: "", password: "", role: "student", invite_code: "" });
  const [error, setError] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault(); setError("");
    try {
      await api.register({ ...f, invite_code: f.role === "teacher" ? f.invite_code : null });
      nav("/login");
    } catch (err) { setError(err.message); }
  };

  return (
    <div className="card auth-box">
      <h2>Register</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={submit}>
        <label>Full name</label><input value={f.name} onChange={set("name")} required minLength={2} />
        <label>Email</label><input type="email" value={f.email} onChange={set("email")} required />
        <label>Password (min 8 chars, letter + digit)</label>
        <input type="password" value={f.password} onChange={set("password")} required minLength={8} />
        <label>I am a</label>
        <select value={f.role} onChange={set("role")}><option value="student">Student</option><option value="teacher">Teacher</option></select>
        {f.role === "teacher" && (<><label>Teacher invite code</label><input value={f.invite_code} onChange={set("invite_code")} required /></>)}
        <button>Create account</button>
      </form>
      <p className="muted">Already registered? <Link to="/login">Login</Link></p>
    </div>
  );
}
