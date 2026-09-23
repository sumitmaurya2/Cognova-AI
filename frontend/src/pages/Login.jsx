import { useEffect, useState } from "react";
import "./Login.css";

const API_URL = `${import.meta.env.VITE_API_URL || "http://localhost:5000/api/auth"}`;

const request = async (path, options = {}) => {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    credentials: "include",
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || "Something went wrong");
  return data;
};

function Login() {
  const query = new URLSearchParams(window.location.search);
  const initialMode = window.location.pathname === "/verify-email"
    ? "verify"
    : window.location.pathname === "/reset-password"
      ? "reset"
      : "login";
  const [mode, setMode] = useState(initialMode);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (initialMode === "verify" && query.get("token")) {
      setBusy(true);
      request(`/verify-email?token=${encodeURIComponent(query.get("token"))}`)
        .then((data) => setMessage(data.message))
        .catch((requestError) => setError(requestError.message))
        .finally(() => setBusy(false));
    }
  }, []);

  const updateField = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const changeMode = (nextMode) => {
    setMode(nextMode);
    setMessage("");
    setError("");
  };

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setError("");
    try {
      let data;
      if (mode === "register") data = await request("/register", { method: "POST", body: JSON.stringify(form) });
      if (mode === "login") data = await request("/login", { method: "POST", body: JSON.stringify({ email: form.email, password: form.password }) });
      if (mode === "forgot") data = await request("/forgot-password", { method: "POST", body: JSON.stringify({ email: form.email }) });
      if (mode === "reset") data = await request(`/reset-password?token=${encodeURIComponent(query.get("token") || "")}`, { method: "POST", body: JSON.stringify({ password: form.password }) });
      if (mode === "resend") data = await request("/resend-verification", { method: "POST", body: JSON.stringify({ email: form.email }) });
      setMessage(data.message || "Done");
      if (mode === "login") setForm({ name: "", email: "", password: "" });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const titles = {
    login: ["Welcome back", "Sign in to continue to Cognova"],
    register: ["Create your account", "Start turning meetings into momentum"],
    forgot: ["Reset your password", "We will send a secure reset link"],
    reset: ["Choose a new password", "Your reset link expires shortly"],
    resend: ["Verify your email", "Get a fresh verification link"],
    verify: ["Email verification", busy ? "Checking your verification link" : "Your verification request is complete"],
  };
  const [title, subtitle] = titles[mode];

  return (
    <main className="auth-layout">
      <section className="auth-visual">
        <span className="brand">Cognova<span>AI</span></span>
        <div>
          <p className="eyebrow">Meeting intelligence, made clear</p>
          <h1>Keep the insight.<br />Lose the busywork.</h1>
          <p className="visual-copy">A focused workspace for transcripts, summaries, and the decisions hiding inside every conversation.</p>
        </div>
        <p className="visual-footer">Secure workspace access</p>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <div className="mobile-brand brand">Cognova<span>AI</span></div>
          <p className="eyebrow">Account access</p>
          <h2>{title}</h2>
          <p className="subtitle">{subtitle}</p>
          {message && <div className="notice success">{message}</div>}
          {error && <div className="notice error">{error}</div>}
          {!['verify'].includes(mode) && (
            <form onSubmit={submit}>
              {mode === "register" && <label>Name<input name="name" value={form.name} onChange={updateField} minLength="2" maxLength="80" required /></label>}
              {mode !== "reset" && <label>Email<input name="email" type="email" value={form.email} onChange={updateField} required /></label>}
              {['login', 'register', 'reset'].includes(mode) && <label>Password<input name="password" type="password" value={form.password} onChange={updateField} minLength="8" maxLength="128" required /></label>}
              <button disabled={busy} type="submit">{busy ? "Please wait..." : mode === "login" ? "Sign in" : mode === "register" ? "Create account" : mode === "forgot" ? "Send reset link" : mode === "reset" ? "Update password" : "Send verification link"}</button>
            </form>
          )}
          <nav className="auth-links">
            {mode === "login" && <><button onClick={() => changeMode("register")}>Create an account</button><button onClick={() => changeMode("forgot")}>Forgot password?</button><button onClick={() => changeMode("resend")}>Resend verification email</button></>}
            {mode !== "login" && <button onClick={() => changeMode("login")}>Back to sign in</button>}
          </nav>
        </div>
      </section>
    </main>
  );
}

export default Login;
