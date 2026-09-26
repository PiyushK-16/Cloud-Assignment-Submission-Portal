import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../services/api";
import StatusBadge from "../components/StatusBadge";
import { fmt } from "../utils/format";

function GradeRow({ s, onSaved, onError }) {
  const [marks, setMarks] = useState(s.marks ?? "");
  const [feedback, setFeedback] = useState(s.feedback ?? "");
  const save = async () => {
    try { await api.grade(s.submission_id, marks, feedback); onSaved(); } catch (e) { onError(e.message); }
  };
  return (
    <tr>
      <td>{s.student_name}<br /><span className="muted">{s.file_name}</span></td>
      <td>{fmt(s.submitted_at)}<br /><StatusBadge status={s.submission_status} /></td>
      <td><button className="secondary" onClick={() => api.download(s.submission_id, s.file_name).catch((e) => onError(e.message))}>Download</button></td>
      <td style={{ minWidth: 220 }}>
        <input type="number" min="0" max={s.max_marks} step="0.5" placeholder={`Marks / ${s.max_marks}`} value={marks} onChange={(e) => setMarks(e.target.value)} />
        <textarea rows={2} placeholder="Written feedback" value={feedback} onChange={(e) => setFeedback(e.target.value)} />
        <button disabled={marks === ""} onClick={save}>Save grade</button>
      </td>
    </tr>
  );
}

export default function TeacherSubmissions() {
  const { id } = useParams();
  const [rows, setRows] = useState([]);
  const [msg, setMsg] = useState({ type: "", text: "" });
  const load = () => api.assignmentSubmissions(id).then(setRows).catch((e) => setMsg({ type: "error", text: e.message }));
  useEffect(() => { load(); }, [id]);

  return (
    <>
      <h2>Submissions {rows[0] && `- ${rows[0].assignment_title}`}</h2>
      {msg.text && <div className={msg.type}>{msg.text}</div>}
      <div className="card">
        {rows.length === 0 ? <p className="muted">No submissions yet.</p> :
          <table>
            <thead><tr><th>Student</th><th>Submitted</th><th>File</th><th>Grade</th></tr></thead>
            <tbody>{rows.map((s) => <GradeRow key={s.submission_id + s.graded_at} s={s}
              onSaved={() => { setMsg({ type: "ok", text: "Grade saved" }); load(); }} onError={(t) => setMsg({ type: "error", text: t })} />)}</tbody>
          </table>}
      </div>
    </>
  );
}
