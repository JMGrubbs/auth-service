const TRANSACTION_PREFIX = "auth:transaction:";
const TRANSACTION_TTL_MS = 5 * 60 * 1000;
const TOKEN_KEY = "auth:access_token";

function base64Url(bytes) {
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

function randomValue(size) {
  const bytes = new Uint8Array(size);
  crypto.getRandomValues(bytes);
  return base64Url(bytes);
}

async function sha256(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return base64Url(new Uint8Array(digest));
}

function transactionKey(state) {
  return `${TRANSACTION_PREFIX}${state}`;
}

function cleanCallbackUrl(callback) {
  callback.searchParams.delete("code");
  callback.searchParams.delete("state");
  return `${callback.pathname}${callback.search}${callback.hash}`;
}

export async function beginLogin({ authUrl, clientId, redirectUri, navigate = (url) => location.assign(url) }) {
  const state = randomValue(32);
  const verifier = randomValue(64);
  const challenge = await sha256(verifier);
  sessionStorage.setItem(transactionKey(state), JSON.stringify({
    verifier,
    clientId,
    redirectUri,
    createdAt: Date.now(),
  }));

  const target = new URL(authUrl);
  target.searchParams.set("client_id", clientId);
  target.searchParams.set("redirect_uri", redirectUri);
  target.searchParams.set("state", state);
  target.searchParams.set("code_challenge", challenge);
  target.searchParams.set("code_challenge_method", "S256");
  navigate(target.toString());
}

export async function completeLogin({
  callbackUrl = location.href,
  tokenEndpoint,
  clientId,
  redirectUri,
  fetcher = fetch,
  replaceUrl = (url) => history.replaceState({}, "", url),
}) {
  const callback = new URL(callbackUrl);
  const code = callback.searchParams.get("code");
  const returnedState = callback.searchParams.get("state");

  // Remove sensitive callback parameters before network activity or validation errors.
  replaceUrl(cleanCallbackUrl(callback));

  if (!code || !returnedState) throw new Error("Invalid authentication state");
  const key = transactionKey(returnedState);
  let transaction;
  try {
    transaction = JSON.parse(sessionStorage.getItem(key));
  } catch {
    transaction = null;
  }
  // A callback attempt consumes this browser-side transaction even if validation or exchange fails.
  sessionStorage.removeItem(key);
  const transactionAge = Date.now() - transaction?.createdAt;
  if (
    !transaction?.verifier
    || !Number.isFinite(transaction.createdAt)
    || transactionAge < 0
    || transactionAge > TRANSACTION_TTL_MS
    || transaction.clientId !== clientId
    || transaction.redirectUri !== redirectUri
  ) {
    throw new Error("Invalid authentication state");
  }

  const response = await fetcher(tokenEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "authorization_code",
      code,
      client_id: clientId,
      redirect_uri: redirectUri,
      code_verifier: transaction.verifier,
    }),
  });
  if (!response.ok) throw new Error("Authorization code exchange failed");
  const token = await response.json();
  if (
    typeof token.access_token !== "string"
    || token.token_type?.toLowerCase() !== "bearer"
    || !Number.isFinite(token.expires_in)
    || token.expires_in <= 0
  ) {
    throw new Error("Token response is invalid");
  }

  const expiresAt = Date.now() + (token.expires_in * 1000);
  sessionStorage.setItem(TOKEN_KEY, JSON.stringify({
    accessToken: token.access_token,
    expiresAt,
  }));
  return {
    accessToken: token.access_token,
    tokenType: token.token_type,
    expiresIn: token.expires_in,
    expiresAt,
  };
}

export function getAccessToken() {
  const raw = sessionStorage.getItem(TOKEN_KEY);
  if (!raw) return null;
  try {
    const token = JSON.parse(raw);
    if (typeof token.accessToken === "string" && token.expiresAt > Date.now()) {
      return token.accessToken;
    }
  } catch {
    // Corrupt or legacy storage is cleared below.
  }
  sessionStorage.removeItem(TOKEN_KEY);
  return null;
}

export function clearAccessToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}
