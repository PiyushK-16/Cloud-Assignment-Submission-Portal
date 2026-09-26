const COLORS = { NOT_SUBMITTED: "#6b7280", SUBMITTED: "#2563eb", LATE: "#d97706", GRADED: "#16a34a" };

export default function StatusBadge({ status }) {
  return <span className="badge" style={{ background: COLORS[status] || "#6b7280" }}>{status.replace("_", " ")}</span>;
}
