import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LoginPage } from "./LoginPage";

const validSearch =
  "?client_id=scrappy-web&redirect_uri=https%3A%2F%2Fscrappy.example.com%2Fauth%2Fcallback" +
  "&state=state-from-scrappy&code_challenge=" + "a".repeat(43) +
  "&code_challenge_method=S256";

describe("LoginPage", () => {
  it("renders an accessible shared sign-in form for the requesting app", () => {
    render(<LoginPage search={validSearch} navigate={vi.fn()} />);

    expect(screen.getByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toHaveAttribute("autocomplete", "email");
    expect(screen.getByLabelText(/^password$/i)).toHaveAttribute("autocomplete", "current-password");
    expect(screen.getByRole("button", { name: /continue securely/i })).toBeEnabled();
  });

  it("blocks login when required authorization parameters are missing", () => {
    render(<LoginPage search="?client_id=scrappy-web" navigate={vi.fn()} />);

    expect(screen.getByRole("alert")).toHaveTextContent(/invalid sign-in request/i);
    expect(screen.queryByRole("button", { name: /continue securely/i })).not.toBeInTheDocument();
  });

  it("submits credentials and navigates only to the server-validated redirect", async () => {
    const navigate = vi.fn();
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        redirect_url: "https://scrappy.example.com/auth/callback?code=one-time&state=state-from-scrappy",
      }),
    });
    const user = userEvent.setup();
    render(<LoginPage search={validSearch} navigate={navigate} fetcher={fetcher} />);

    await user.type(screen.getByLabelText(/email address/i), "user@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "correct horse battery staple");
    await user.click(screen.getByRole("button", { name: /continue securely/i }));

    expect(fetcher).toHaveBeenCalledWith(
      "/api/v1/oauth/authorize",
      expect.objectContaining({ method: "POST" }),
    );
    expect(navigate).toHaveBeenCalledWith(
      "https://scrappy.example.com/auth/callback?code=one-time&state=state-from-scrappy",
    );
  });

  it("shows a generic error and re-enables the form after failed credentials", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Invalid email or password" }),
    });
    const user = userEvent.setup();
    render(<LoginPage search={validSearch} navigate={vi.fn()} fetcher={fetcher} />);

    await user.type(screen.getByLabelText(/email address/i), "user@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "wrong password");
    await user.click(screen.getByRole("button", { name: /continue securely/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/email or password/i);
    expect(screen.getByRole("button", { name: /continue securely/i })).toBeEnabled();
  });
});
