import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthProvider";
import { getCurrentUser } from "../services/User";

const profileFields = [
  { label: "Display name", value: "Add your name" },
  { label: "Email address", key: "email", value: "Add your email" },
  { label: "Phone number", value: "Add a phone number" },
  { label: "Location", value: "Add your location" },
  { label: "Job title", value: "Add your job title" },
  { label: "Organization", value: "Add your organization" },
];

const connectedApps = [
  { name: "Your first application", description: "Connected application details will appear here.", status: "Placeholder", initials: "01" },
  { name: "Another application", description: "Add services that use this account for secure sign-in.", status: "Placeholder", initials: "02" },
];

function SectionHeading({ eyebrow, title, description, action }) {
  return (
    <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-purple-300">{eyebrow}</p>
        <h2 className="mt-1 text-xl font-semibold text-white">{title}</h2>
        {description && <p className="mt-1 text-sm text-slate-400">{description}</p>}
      </div>
      {action && (
        <button type="button" disabled title="Connect this action when profile editing is implemented." className="w-fit cursor-not-allowed rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-400">
          {action}
        </button>
      )}
    </div>
  );
}

export default function UserPage() {
  const { user, isAuthenticated } = useAuth();
  const [apiData, setApiData] = useState(null);
  const [apiLoading, setApiLoading] = useState(true);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    let active = true;

    const fetchUserData = async () => {
      try {
        const data = await getCurrentUser();
        if (active) setApiData(data);
      } catch (error) {
        if (active) setApiError(error?.response?.data?.detail || "Profile details could not be refreshed.");
      } finally {
        if (active) setApiLoading(false);
      }
    };

    fetchUserData();
    return () => {
      active = false;
    };
  }, []);

  const profile = useMemo(() => {
    const contextUser = typeof user === "object" && user ? user : {};
    const username = apiData?.username || apiData?.email || contextUser.username || contextUser.email || (typeof user === "string" ? user : "") || "Your name";
    const email = apiData?.email || contextUser.email || "Add your email";

    return {
      username,
      email,
      initials: username === "Your name" ? "YN" : username.split(/[\s@._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0].toUpperCase()).join(""),
      role: apiData?.is_admin ? "Administrator" : "Member",
    };
  }, [apiData, user]);

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-950 text-white">
      <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-16 h-96 bg-[radial-gradient(circle_at_25%_0%,rgba(147,51,234,0.2),transparent_55%)]" />

      <main className="relative mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        {apiError && (
          <div role="alert" className="mb-6 rounded-xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
            {apiError} Showing saved account information instead.
          </div>
        )}

        <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/90 shadow-2xl shadow-purple-950/20">
          <div className="h-32 bg-gradient-to-r from-purple-700 via-violet-600 to-indigo-600 sm:h-40" />
          <div className="px-6 pb-7 sm:px-8">
            <div className="-mt-12 flex flex-col gap-5 sm:-mt-14 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
                <div className="flex h-24 w-24 items-center justify-center rounded-2xl border-4 border-slate-900 bg-slate-800 text-2xl font-semibold text-purple-200 shadow-xl sm:h-28 sm:w-28">
                  {apiLoading ? "…" : profile.initials}
                </div>
                <div className="pb-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h1 className="text-3xl font-semibold tracking-tight">{apiLoading ? "Loading profile…" : profile.username}</h1>
                    <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-xs font-medium text-emerald-300">{isAuthenticated ? "Active" : "Inactive"}</span>
                  </div>
                  <p className="mt-1 text-sm text-slate-400">{profile.role} · Account profile</p>
                </div>
              </div>
              <button type="button" disabled title="Connect this action when profile editing is implemented." className="w-fit cursor-not-allowed rounded-lg bg-purple-500/50 px-5 py-2.5 text-sm font-semibold text-purple-100">Edit profile</button>
            </div>
          </div>
        </section>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.55fr_0.8fr]">
          <div className="space-y-6">
            <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/80">
              <SectionHeading eyebrow="Personal information" title="About you" description="Basic information associated with your account." action="Edit details" />
              <dl className="grid gap-px bg-white/10 sm:grid-cols-2">
                {profileFields.map((field) => (
                  <div key={field.label} className="bg-slate-900 px-6 py-5">
                    <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{field.label}</dt>
                    <dd className={`mt-2 text-sm ${field.key === "email" ? "text-slate-200" : "italic text-slate-500"}`}>
                      {field.key === "email" ? profile.email : field.value}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>

            <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/80">
              <SectionHeading eyebrow="Applications" title="Connected apps" description="Applications that use this account for sign-in." action="Manage apps" />
              <div className="divide-y divide-white/10">
                {connectedApps.map((app) => (
                  <article key={app.name} className="flex items-center gap-4 px-6 py-5">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-purple-400/10 font-mono text-xs font-semibold text-purple-300">{app.initials}</div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-medium text-slate-200">{app.name}</h3>
                      <p className="mt-1 text-sm text-slate-500">{app.description}</p>
                    </div>
                    <span className="hidden rounded-full border border-white/10 px-2.5 py-1 text-xs text-slate-500 sm:block">{app.status}</span>
                  </article>
                ))}
              </div>
            </section>
          </div>

          <aside className="space-y-6">
            <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/80">
              <SectionHeading eyebrow="Account" title="Security" />
              <div className="space-y-5 px-6 py-6">
                <div>
                  <div className="flex justify-between gap-4 text-sm"><span className="text-slate-300">Password</span><span className="text-emerald-300">Configured</span></div>
                  <p className="mt-1 text-xs text-slate-500">Add password management here later.</p>
                </div>
                <div className="border-t border-white/10 pt-5">
                  <div className="flex justify-between gap-4 text-sm"><span className="text-slate-300">Two-factor authentication</span><span className="text-amber-300">Not configured</span></div>
                  <p className="mt-1 text-xs text-slate-500">Reserve this area for stronger account protection.</p>
                </div>
              </div>
            </section>

            <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/80">
              <SectionHeading eyebrow="Preferences" title="Experience" />
              <dl className="space-y-4 px-6 py-6 text-sm">
                <div className="flex justify-between gap-4"><dt className="text-slate-400">Language</dt><dd className="text-slate-200">English</dd></div>
                <div className="flex justify-between gap-4"><dt className="text-slate-400">Time zone</dt><dd className="italic text-slate-500">Add later</dd></div>
                <div className="flex justify-between gap-4"><dt className="text-slate-400">Theme</dt><dd className="text-slate-200">Dark</dd></div>
              </dl>
            </section>

            <section className="rounded-2xl border border-dashed border-purple-400/30 bg-purple-400/5 p-6">
              <p className="text-sm font-medium text-purple-200">Ready for your data</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">Placeholder values are intentionally visible so you can connect profile editing, preferences, and application data later.</p>
            </section>
          </aside>
        </div>
      </main>
    </div>
  );
}
