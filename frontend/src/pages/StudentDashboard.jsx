import { useEffect, useState } from "react";
import { api } from "../services/api";
import { fmt } from "../utils/format";

export default function StudentDashboard() {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.studentDashboard().then(setD).catch((e) => setError(e.message)); }, []);
  if (error) return <div className="error">{error}</div>;
  if (!d) return <p>Loading...</p>;
  const stats = [["Total", d.total_assignments], ["Pending", d.pending_assignments], ["Submitted", d.submitted_assignments], ["Late", d.late_assignments], ["Graded", d.graded_assignments]];
  return (
    <>
      <h2>{d.welcome}</h2>
      <div className="grid">{stats.map(([k, v]) => <div className="stat" key={k}><b>{v}</b>{k}</div>)}</div>
      <div className="card">
        <h3>Upcoming deadlines</h3>
        {d.upcoming_deadlines.length === 0 ? <p className="muted">Nothing due - great job!</p> :
          <ul>{d.upcoming_deadlines.map((a) => <li key={a.assignment_id}>{a.title} <span className="muted">({a.course_name}) - due {fmt(a.deadline)}</span></li>)}</ul>}
      </div>
      <div className="card">
        <h3>Recent feedback</h3>
        {d.recent_feedback.length === 0 ? <p className="muted">No graded work yet.</p> :
          d.recent_feedback.map((s) => (
            <div key={s.submission_id}><b>{s.assignment_title}</b> - {s.marks}/{s.max_marks}<br /><span className="muted">{s.feedback || "No written feedback"}</span><hr /></div>
          ))}
      </div>
    </>
  );
}
