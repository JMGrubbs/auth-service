import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearAccessToken,
  completeLogin,
  getAccessToken,
} from "../public/auth-client.js";

const storage = new Map();

beforeEach(() => {
  storage.clear();
  vi.useRealTimers();
  vi.stubGlobal("sessionStorage", {
    getItem: (key) => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: (key) => storage.delete(key),
  });
});

function seedTransaction(state, overrides = {}) {
  sessionStorage.setItem(`auth:transaction:${state}`, JSON.stringify({
    verifier: "v".repeat(64),
    clientId: "scrappy-web",
    redirectUri: "https://scrappy.example.com/auth/callback",
    createdAt: Date.now(),
    ...overrides,
  }));
}

describe("completeLogin", () => {
  it("cleans the callback URL, exchanges with PKCE, and stores an expiring token", async () => {
    seedTransaction("expected-state");
    const replaceUrl = vi.fn();
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "browser-token", token_type: "bearer", expires_in: 3600 }),
    });

    const result = await completeLogin({
      callbackUrl: "https://scrappy.example.com/auth/callback?keep=yes&code=one-time&state=expected-state",
      tokenEndpoint: "https://auth.example.com/api/v1/oauth/token",
      clientId: "scrappy-web",
      redirectUri: "https://scrappy.example.com/auth/callback",
      fetcher,
      replaceUrl,
    });

    expect(replaceUrl).toHaveBeenCalledWith("/auth/callback?keep=yes");
    expect(fetcher).toHaveBeenCalledWith(
      "https://auth.example.com/api/v1/oauth/token",
      expect.objectContaining({ method: "POST" }),
    );
    expect(sessionStorage.getItem("auth:transaction:expected-state")).toBeNull();
    expect(getAccessToken()).toBe("browser-token");
    expect(result.accessToken).toBe("browser-token");
  });

  it("uses state-keyed transactions so another pending login is not overwritten", async () => {
    seedTransaction("first-state");
    seedTransaction("second-state", { verifier: "x".repeat(64) });
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "first-token", token_type: "bearer", expires_in: 60 }),
    });

    await completeLogin({
      callbackUrl: "https://scrappy.example.com/auth/callback?code=first-code&state=first-state",
      tokenEndpoint: "https://auth.example.com/api/v1/oauth/token",
      clientId: "scrappy-web",
      redirectUri: "https://scrappy.example.com/auth/callback",
      fetcher,
      replaceUrl: vi.fn(),
    });

    expect(sessionStorage.getItem("auth:transaction:first-state")).toBeNull();
    expect(sessionStorage.getItem("auth:transaction:second-state")).not.toBeNull();
  });

  it("cleans the URL and rejects a callback with no matching transaction", async () => {
    seedTransaction("expected-state");
    const replaceUrl = vi.fn();

    await expect(
      completeLogin({
        callbackUrl: "https://scrappy.example.com/auth/callback?code=one-time&state=attacker-state",
        tokenEndpoint: "https://auth.example.com/api/v1/oauth/token",
        clientId: "scrappy-web",
        redirectUri: "https://scrappy.example.com/auth/callback",
        replaceUrl,
      }),
    ).rejects.toThrow(/state/i);
    expect(replaceUrl).toHaveBeenCalledWith("/auth/callback");
  });

  it("rejects and removes a stale browser transaction", async () => {
    seedTransaction("stale-state", { createdAt: Date.now() - (6 * 60 * 1000) });

    await expect(
      completeLogin({
        callbackUrl: "https://scrappy.example.com/auth/callback?code=one-time&state=stale-state",
        tokenEndpoint: "https://auth.example.com/api/v1/oauth/token",
        clientId: "scrappy-web",
        redirectUri: "https://scrappy.example.com/auth/callback",
        replaceUrl: vi.fn(),
      }),
    ).rejects.toThrow(/state/i);
    expect(sessionStorage.getItem("auth:transaction:stale-state")).toBeNull();
  });

  it("removes and refuses an expired browser token", () => {
    sessionStorage.setItem("auth:access_token", JSON.stringify({
      accessToken: "expired-token",
      expiresAt: Date.now() - 1,
    }));

    expect(getAccessToken()).toBeNull();
    expect(sessionStorage.getItem("auth:access_token")).toBeNull();
  });

  it("clears the browser token explicitly", () => {
    sessionStorage.setItem("auth:access_token", JSON.stringify({
      accessToken: "token",
      expiresAt: Date.now() + 60_000,
    }));
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });
});
