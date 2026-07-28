const steps = [
  { number: '01', title: 'Create one account', description: 'Set up a single identity you can use across all connected applications.' },
  { number: '02', title: 'Sign in securely', description: 'Use one trusted sign-in experience instead of creating and managing credentials in every app.' },
  { number: '03', title: 'Manage your data', description: 'Review and control the information your connected applications store from one central place.' },
];

const capabilities = ['One account', 'Central sign-in', 'Connected applications', 'Profile management', 'App data controls', 'Privacy and security'];

function ArrowIcon() {
  return (
    <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14m-5-5 5 5-5 5" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="m5 12 4 4L19 6" />
    </svg>
  );
}

export default function About() {
  return (
    <div className="min-h-[calc(100vh-4rem)] overflow-hidden bg-slate-950 text-white">
      <section className="relative isolate px-4 pb-20 pt-20 sm:px-6 sm:pb-28 sm:pt-28 lg:px-8">
        <div aria-hidden="true" className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0%,rgba(147,51,234,0.24),transparent_42%)]" />
        <div aria-hidden="true" className="absolute inset-0 -z-10 opacity-30 [background-image:linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] [background-size:48px_48px]" />
        <div className="mx-auto max-w-5xl text-center">
          <div className="mx-auto mb-8 flex w-fit items-center gap-2 rounded-full border border-purple-400/30 bg-purple-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-purple-200">
            <span className="h-2 w-2 rounded-full bg-purple-400 shadow-[0_0_12px_rgba(192,132,252,.9)]" />
            About Your Account
          </div>
          <h1 className="mx-auto max-w-4xl text-balance text-5xl font-semibold leading-[1.05] tracking-tight text-white sm:text-6xl lg:text-7xl">
            One account for all of your
            <span className="bg-gradient-to-r from-purple-300 to-indigo-300 bg-clip-text text-transparent"> connected apps.</span>
          </h1>
          <p className="mx-auto mt-7 max-w-2xl text-lg leading-8 text-slate-300 sm:text-xl">
            Create your account once, sign in securely across the applications in this ecosystem, and manage the data those apps keep—all from one central place.
          </p>
          <div className="mx-auto mt-12 flex max-w-xl items-center justify-center gap-3 text-sm text-slate-400">
            <span className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-purple-300">your account</span>
            <ArrowIcon />
            <span className="rounded-lg border border-purple-500/40 bg-purple-500/10 px-3 py-2 font-mono text-purple-200">secure sign-in</span>
            <ArrowIcon />
            <span className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-indigo-300">your apps</span>
          </div>
        </div>
      </section>

      <section className="border-y border-white/10 bg-white/[0.03] px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 max-w-2xl text-left">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-purple-300">How it works</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">A simpler way to access everything</h2>
            <p className="mt-4 leading-7 text-slate-400">Your identity, access, and application data stay organized behind one consistent account experience.</p>
          </div>
          <div className="grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 md:grid-cols-3">
            {steps.map((step) => (
              <article key={step.number} className="bg-slate-950 p-8 text-left">
                <p className="font-mono text-sm text-purple-300">{step.number}</p>
                <h3 className="mt-8 text-xl font-semibold text-white">{step.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-400">{step.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 py-20 sm:px-6 sm:py-28 lg:px-8">
        <div className="mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[0.9&r_1.1fr]">
          <div className="text-left">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-purple-300">You stay in control</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Your account and app data, together.</h2>
            <p className="mt-5 max-w-xl leading-7 text-slate-400">See which applications are connected to your account, update your profile, and manage the data created through those applications from a single dashboard.</p>
            <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
              {capabilities.map((capability) => (
                <div key={capability} className="flex items-center gap-3 text-sm text-slate-300">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-purple-400/15 text-purple-300"><CheckIcon /></span>
                  {capability}
                </div>
              ))}
            </div>
          </div>
          <div className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl shadow-purple-950/30">
            <div className="flex items-center gap-2 border-b border-slate-700 px-5 py-4">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-400/80" /><span className="h-2.5 w-2.5 rounded-full bg-amber-300/80" /><span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
              <span className="ml-3 font-mono text-xs text-slate-500">account overview</span>
            </div>
            <div className="space-y-4 p-6 text-left sm:p-8">
              <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-purple-300">Identity</p>
                <p className="mt-2 text-sm text-slate-300">One secure profile shared across your connected applications.</p>
              </div>
              <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-300">Application data</p>
                <p className="mt-2 text-sm text-slate-300">A central place to review and manage data from the apps you use.</p>
              </div>
            </div>
            <div className="border-t border-slate-700 bg-slate-950/70 px-6 py-4 text-left text-xs text-slate-500">More applications and account controls can be added as the ecosystem grows.</div>
          </div>
        </div>
      </section>

      <section className="border-t border-white/10 px-4 py-16 text-center sm:px-6 lg:px-8">
        <p className="mx-auto max-w-2xl text-balance text-2xl font-medium leading-9 text-slate-200">One trusted account. Every connected application. Your data under your control.</p>
      </section>
    </div>
  );
}
