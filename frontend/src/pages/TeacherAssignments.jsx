import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { fmt } from "../utils/format";

const EMPTY = { course_id: "", title: "", description: "", deadline: "", max_marks: 100, allowed_file_types: "pdf", max_file_size_mb: 10, allow_late: true, allow_resubmission: true };

export default function TeacherAssignments() {
  const [courses, setCourses] = useState([]);
  const [items, setItems] = useState([]);
  const [courseName, setCourseName] = useState("");
  const [f, setF] = useState(EMPTY);
  const [msg, setMsg] = useState({ type: "", text: "" });

  const load = async () => { setCourses(await api.courses()); setItems(await api.assignments()); };
  useEffect(() => { load().catch((e) => setMsg({ type: "error", text: e.message })); }, []);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  const addCourse = async (e) => {
    e.preventDefault();
    try { await api.createCourse(courseName); setCourseName(""); await load(); } catch (err) { setMsg({ type: "error", text: err.message }); }
  };

  const create = async (e) => {
    e.preventDefault();
    try {
      await api.createAssignment({ ...f, course_id: f.course_id || courses[0]?.course_id, deadline: new Date(f.deadline).toISOString(), max_marks: Number(f.max_marks), max_file_size_mb: Number(f.max_file_size_mb) });
      setF(EMPTY); setMsg({ type: "ok", text: "Assignment created" }); await load();
    } catch (err) { setMsg({ type: "error", text: err.message }); }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this assignment and ALL its submissions?")) return;
    try { await api.deleteAssignment(id); await load(); } catch (err) { setMsg({ type: "error", text: err.message }); }
  };

  return (
    <>
      <h2>Manage Assignments</h2>
      {msg.text && <div className={msg.type}>{msg.text}</div>}
      <div className="card">
        <h3>New course</h3>
        <form className="row" onSubmit={addCourse}>
          <input style={{ flex: 1, margin: 0 }} placeholder="e.g. Cloud Computing" value={courseName} onChange={(e) => setCourseName(e.target.value)} required minLength={2} />
          <button>Add course</button>
        </form>
      </div>
      <div className="card">
        <h3>Create assignment</h3>
        <form onSubmit={create}>
          <label>Course</label>
          <select value={f.course_id} onChange={set("course_id")} required>
            <option value="">-- select --</option>
            {courses.map((c) => <option key={c.course_id} value={c.course_id}>{c.course_name}</option>)}
          </select>
          <label>Title</label><input value={f.title} onChange={set("title")} required minLength={3} />
          <label>Description</label><textarea rows={3} value={f.description} onChange={set("description")} />
          <label>Deadline (your local time)</label><input type="datetime-local" value={f.deadline} onChange={set("deadline")} required />
          <div className="row">
            <div><label>Max marks</label><input type="number" min="1" value={f.max_marks} onChange={set("max_marks")} /></div>
            <div><label>Allowed types (comma separated)</label><input value={f.allowed_file_types} onChange={set("allowed_file_types")} /></div>
            <div><label>Max size (MB)</label><input type="number" min="1" max="50" value={f.max_file_size_mb} onChange={set("max_file_size_mb")} /></div>
          </div>
          <label><input type="checkbox" style={{ width: "auto" }} checked={f.allow_late} onChange={set("allow_late")} /> Allow late submissions (marked LATE)</label><br />
          <label><input type="checkbox" style={{ width: "auto" }} checked={f.allow_resubmission} onChange={set("allow_resubmission")} /> Allow resubmission</label><br /><br />
          <button>Create assignment</button>
        </form>
      </div>
      {items.map((a) => (
        <div className="card row" key={a.assignment_id}>
          <div style={{ flex: 1 }}><b>{a.title}</b><br /><span className="muted">{a.course_name} | due {fmt(a.deadline)} | {a.submission_count} submission(s)</span></div>
          <Link className="btn" to={`/teacher/assignments/${a.assignment_id}`}>Review</Link>
          <button className="danger" onClick={() => remove(a.assignment_id)}>Delete</button>
        </div>
      ))}
    </>
  );
}
