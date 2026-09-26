import { useEffect, useState } from "react";
import { api } from "../services/api";
import StatusBadge from "../components/StatusBadge";
import { bytes, fmt } from "../utils/format";

export default function MySubmissions() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => { api.mySubmissions().then(setRows).catch((e) => setError(e.message)); }, []);
  const dl = (s) => api.download(s.submission_id, s.file_name).catch((e) => setError(e.message));

  return (
    <>
      <h2>My Submissions</h2>
      {error && <div className="error">{error}</div>}
      {rows.length === 0 && <p className="muted">You have not submitted anything yet.</p>}
      {rows.map((s) => (
        <div className="card" key={s.submission_id}>
          <div className="row"><h3 style={{ margin: 0 }}>{s.assignment_title}</h3><StatusBadge status={s.submission_status} /></div>
          <p className="muted">{s.file_name} ({bytes(s.file_size)}) | submitted {fmt(s.submitted_at)} | attempt #{s.attempt_count}</p>
          {s.submission_status === "GRADED" && (
            <p><b>Marks: {s.marks} / {s.max_marks}</b><br />Feedback: {s.feedback || "-"}<br /><span className="muted">Graded {fmt(s.graded_at)}</span></p>
          )}
          <button className="secondary" onClick={() => dl(s)}>Download my file</button>
        </div>
      ))}
    </>
  );
}
