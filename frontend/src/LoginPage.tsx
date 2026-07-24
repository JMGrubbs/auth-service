import { FormEvent, useMemo, useState } from "react";

type Fetcher = typeof fetch;

type LoginPageProps = {
  search?: string;
  navigate?: (url: string) => void;
  fetcher?: Fetcher;
};

type AuthorizationParams = {
  client_id: string;
  redirect_uri: string;
  state: string;
  code_challenge: string;
  code_challenge_method: "S256";
};

const challengePattern = /^[A-Za-z0-9_-]{43,128}$/;

function parseAuthorization(search: string): AuthorizationParams | null {
  const params = new URLSearchParams(search);
  const client_id = params.get("client_id") ?? "";
  const redirect_uri = params.get("redirect_uri") ?? "";
  const state = params.get("state") ?? "";
  const code_challenge = params.get("code_challenge") ?? "";
  const code_challenge_method = params.get("code_challenge_method");

  if (
    !/^[A-Za-z0-9._-]{3,80}$/.test(client_id) ||
    redirect_uri.length < 10 ||
    state.length < 8 ||
    state.length > 512 ||
    !challengePattern.test(code_challenge) ||
    code_challenge_method !== "S256"
  ) {
    return null;
  }
  return { client_id, redirect_uri, state, code_challenge, code_challenge_method };
}

export function LoginPage({
  search = window.location.search,
  navigate = (url) => window.location.assign(url),
  fetcher = fetch,
}: LoginPageProps) {
  const authorization = useMemo(() => parseAuthorization(search), [search]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!authorization || submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const response = await fetcher("/api/v1/oauth/authorize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...authorization, email, password }),
      });
      const body = await response.json();
      if (!response.ok || typeof body.redirect_url !== "string") {
        throw new Error("Invalid email or password");
      }
      navigate(body.redirect_url);
    } catch {
      setError("We couldn't sign you in. Check your email or password and try again.");
      setSubmitting(false);
    }
  }

  if (!authorization) {
    return (
      <main className="shell">
        <section className="login-card request-error" aria-labelledby="request-title" role="alert">
          <Brand />
          <div className="status-icon" aria-hidden="true">!</div>
          <h1 id="request-title">Invalid sign-in request</h1>
          <p>
            This application did not provide a complete, secure login request. Return to the app and try again.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <section className="login-card" aria-labelledby="login-title">
        <Brand />
        <header className="intro">
          <p className="eyebrow">One account. Every app.</p>
          <h1 id="login-title">Welcome back</h1>
          <p>Sign in once through your trusted identity service to continue securely.</p>
        </header>

        <form onSubmit={submit}>
          <label htmlFor="email">Email address</label>
          <div className="field-wrap">
            <span aria-hidden="true">@</span>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              inputMode="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
              disabled={submitting}
            />
          </div>

          <div className="password-row">
            <label htmlFor="password">Password</label>
            <span>Protected with PKCE</span>
          </div>
          <div className="field-wrap">
            <span aria-hidden="true">●</span>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              required
              disabled={submitting}
            />
          </div>

          {error && <p className="form-error" role="alert">{error}</p>}

          <button type="submit" disabled={submitting}>
            <span>{submitting ? "Signing you in…" : "Continue securely"}</span>
            <span aria-hidden="true">→</span>
          </button>
        </form>

        <footer>
          <span className="shield" aria-hidden="true">✓</span>
          Your credentials stay with Auth Service. The requesting app receives a one-time code, never your password.
        </footer>
      </section>
      <p className="legal">Centralized identity · Encrypted in transit · Short-lived access</p>
    </main>
  );
}

function Brand() {
  return (
    <div className="brand" aria-label="Auth Service">
      <div className="brand-mark" aria-hidden="true"><span /></div>
      <span>AUTH<span>/</span>SERVICE</span>
    </div>
  );
}
