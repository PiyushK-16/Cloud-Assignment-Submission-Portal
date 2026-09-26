// API service layer: the ONLY place that talks to the backend.
const BASE = import.meta.env.VITE_API_BASE_URL || "/api";
const TOKEN_KEY = "portal_token";
const USER_KEY = "portal_user";

export const auth = {
  token: () => sessionStorage.getItem(TOKEN_KEY), // sessionStorage: cleared when the tab closes
  user: () => JSON.parse(sessionStorage.getItem(USER_KEY) || "null"),
  save: (token, user) => { sessionStorage.setItem(TOKEN_KEY, token); sessionStorage.setItem(USER_KEY, JSON.stringify(user)); },
  clear: () => { sessionStorage.removeItem(TOKEN_KEY); sessionStorage.removeItem(USER_KEY); },
};

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

function errorMessage(detail) {
  if (Array.isArray(detail)) return detail.map((d) => `${(d.loc || []).slice(-1)[0]}: ${d.msg}`).join("; ");
  return typeof detail === "string" ? detail : "Something went wrong";
}

async function request(path, { method = "GET", body, form } = {}) {
  const headers = {};
  if (auth.token()) headers.Authorization = `Bearer ${auth.token()}`;
  if (body) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body: form || (body ? JSON.stringify(body) : undefined) });
  } catch {
    throw new ApiError("Cannot reach the server. Check your internet connection and try again.", 0);
  }
  if (res.status === 401 && auth.token()) {
    auth.clear();
    window.dispatchEvent(new Event("auth-expired")); // session expired -> AuthContext logs the user out
  }
  if (!res.ok) {
    let detail; try { detail = (await res.json()).detail; } catch { /* non-JSON error */ }
    throw new ApiError(errorMessage(detail), res.status);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  register: (b) => request("/register", { method: "POST", body: b }),
  login: (b) => request("/login", { method: "POST", body: b }),
  logout: () => request("/logout", { method: "POST" }),
  studentDashboard: () => request("/dashboard/student"),
  teacherDashboard: () => request("/dashboard/teacher"),
  courses: () => request("/courses"),
  createCourse: (course_name) => request("/courses", { method: "POST", body: { course_name } }),
  enroll: (id) => request(`/courses/${id}/enroll`, { method: "POST" }),
  assignments: () => request("/assignments"),
  createAssignment: (b) => request("/assignments", { method: "POST", body: b }),
  deleteAssignment: (id) => request(`/assignments/${id}`, { method: "DELETE" }),
  submit: (id, file) => { const f = new FormData(); f.append("file", file); return request(`/assignments/${id}/submit`, { method: "POST", form: f }); },
  mySubmissions: () => request("/submissions/me"),
  assignmentSubmissions: (id) => request(`/assignments/${id}/submissions`),
  grade: (id, marks, feedback) => request(`/submissions/${id}/grade`, { method: "POST", body: { marks: Number(marks), feedback } }),
  // Private file download: fetch with the auth header, then hand the blob to the browser.
  async download(id, fileName) {
    const res = await fetch(`${BASE}/submissions/${id}/download`, { headers: { Authorization: `Bearer ${auth.token()}` } });
    if (!res.ok) throw new ApiError("Download not allowed or file unavailable", res.status);
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a");
    a.href = url; a.download = fileName; a.click();
    URL.revokeObjectURL(url);
  },
};
