import { useEffect, useState } from "react";
import { api } from "../services/api";
import StatusBadge from "../components/StatusBadge";
import { bytes, fmt, isPast } from "../utils/format";

export default function StudentAssignments() {
  const [courses, setCourses] = useState([]);
  const [items, setItems] = useState([]);
  const [msg, setMsg] = useState({ type: "", text: "" });
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    try { setCourses(await api.courses()); setItems(await api.assignments()); }
    catch (e) { setMsg({ type: "error", text: e.message }); }
  };
  useEffect(() => { load(); }, []);

  const enroll = async (id) => { await api.enroll(id); load(); };

  const upload = async (a, file) => {
    if (!file) return;
    const maxBytes = a.max_file_size_mb * 1048576;
    // Client-side checks are for UX only; the server re-validates everything.
    const ext = file.name.split(".").pop().toLowerCase();
    if (!a.allowed_file_types.includes(ext)) return setMsg({ type: "error", text: `Allowed types: ${a.allowed_file_types.join(", ")}` });
    if (file.size > maxBytes) return setMsg({ type: "error", text: `File exceeds ${a.max_file_size_mb} MB` });
    setBusyId(a.assignment_id); setMsg({ type: "", text: "" });
    try {
      const s = await api.submit(a.assignment_id, file);
      setMsg({ type: "ok", text: `Uploaded "${s.file_name}" (${bytes(s.file_size)}) - status: ${s.submission_status}` });
      load();
    } catch (e) { setMsg({ type: "error", text: e.message }); } finally { setBusyId(null); }
  };

  return (
    <>
      <h2>Assignments</h2>
      {msg.text && <div className={msg.type}>{msg.text}</div>}
      <div className="card">
        <h3>Courses</h3>
        {courses.map((c) => (
          <div className="row" key={c.course_id}>
            <span>{c.course_name} <span className="muted">- {c.teacher_name}</span></span>
            {c.enrolled ? <span className="badge" style={{ background: "#16a34a" }}>Enrolled</span> : <button onClick={() => enroll(c.course_id)}>Enroll</button>}
          </div>
        ))}
      </div>
      {items.length === 0 && <p className="muted">Enroll in a course to see its assignments.</p>}
      {items.map((a) => {
        const graded = a.my_status === "GRADED";
        const closed = isPast(a.deadline) && !a.allow_late;
        const locked = graded || closed || (a.my_status !== "NOT_SUBMITTED" && !a.allow_resubmission);
        return (
          <div className="card" key={a.assignment_id}>
            <div className="row"><h3 style={{ margin: 0 }}>{a.title}</h3><StatusBadge status={a.my_status} /></div>
            <p>{a.description}</p>
            <p className="muted">{a.course_name} | Due {fmt(a.deadline)} | Max marks {a.max_marks} | Types: {a.allowed_file_types.join(", ")} | Max {a.max_file_size_mb} MB
              {isPast(a.deadline) && (a.allow_late ? " | Past due - submissions will be marked LATE" : " | Closed")}</p>
            <input type="file" disabled={locked || busyId === a.assignment_id} onChange={(e) => { upload(a, e.target.files[0]); e.target.value = ""; }} />
            {locked && <span className="muted">{graded ? "Already graded" : "Submissions locked"}</span>}
            {busyId === a.assignment_id && <span className="muted">Uploading...</span>}
          </div>
        );
      })}
    </>
  );
}
