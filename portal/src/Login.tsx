import { FormEvent, useState } from "react";
import { login } from "./api";

export default function Login({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(username, password);
      onSuccess();
    } catch {
      setError("Invalid credentials. Check your username and password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="brand-icon">◆</span>
          <h1>Command Center</h1>
          <p>Your empire command deck</p>
        </div>
        <form onSubmit={handleSubmit}>
          <label>
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? "Entering..." : "Enter Command Deck"}
          </button>
        </form>
      </div>
      <style>{`
        .login-page {
          min-height: 100vh;
          display: grid;
          place-items: center;
          padding: 2rem;
        }
        .login-card {
          width: 100%;
          max-width: 400px;
          background: var(--bg-panel);
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 2.5rem;
          box-shadow: 0 0 60px var(--accent-glow);
        }
        .login-brand {
          text-align: center;
          margin-bottom: 2rem;
        }
        .brand-icon {
          font-size: 2rem;
          color: var(--accent);
          display: block;
          margin-bottom: 0.5rem;
        }
        .login-brand h1 {
          font-size: 1.75rem;
          font-weight: 600;
        }
        .login-brand p {
          color: var(--text-muted);
          margin-top: 0.25rem;
        }
        form label {
          display: block;
          margin-bottom: 1rem;
          font-size: 0.875rem;
          color: var(--text-muted);
        }
        form input {
          display: block;
          width: 100%;
          margin-top: 0.35rem;
          padding: 0.75rem 1rem;
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 8px;
          color: var(--text);
          font-size: 1rem;
        }
        form input:focus {
          outline: none;
          border-color: var(--accent);
          box-shadow: 0 0 0 3px var(--accent-glow);
        }
        form button {
          width: 100%;
          margin-top: 0.5rem;
          padding: 0.875rem;
          background: var(--accent);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 500;
        }
        form button:disabled {
          opacity: 0.6;
        }
        .error {
          color: var(--danger);
          font-size: 0.875rem;
          margin-bottom: 0.5rem;
        }
      `}</style>
    </div>
  );
}
