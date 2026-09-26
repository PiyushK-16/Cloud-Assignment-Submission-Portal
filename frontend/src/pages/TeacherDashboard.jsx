import { useEffect, useState } from "react";
import { api } from "../services/api";
import { fmt } from "../utils/format";

export default function TeacherDashboard() {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.teacherDashboard().then(setD).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="error">{error}</div>;
  if (!d) return <p>Loading...</p>;
  const stats = [["Assignments", d.total_assignments], ["Students", d.total_students], ["Submissions", d.total_submissions], ["Pending review", d.pending_reviews], ["Late", d.late_submissions], ["Graded", d.graded_submissions]];
  return (
    <>
      <h2>{d.welcome}</h2>
      <div className="grid">{stats.map(([k, v]) => <div className="stat" key={k}><b>{v}</b>{k}</div>)}</div>
      <div className="card">
        <h3>Recent uploads</h3>
        {d.recent_uploads.length === 0 ? <p className="muted">No submissions yet.</p> :
          <table><tbody>{d.recent_uploads.map((s) => (
            <tr key={s.submission_id}><td>{s.student_name}</td><td>{s.assignment_title}</td><td>{s.submission_status}</td><td>{fmt(s.submitted_at)}</td></tr>
          ))}</tbody></table>}
      </div>
      <div className="card">
        <h3>Upcoming deadlines</h3>
        <ul>{d.upcoming_deadlines.map((a) => <li key={a.assignment_id}>{a.title} - {fmt(a.deadline)}</li>)}</ul>
      </div>
    </>
  );
}
