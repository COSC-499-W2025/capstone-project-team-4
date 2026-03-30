import MainNav from "@/components/custom/Home/MainNav";

export default function AuthShell({
  title,
  subtitle,
  children,
  helperTitle = "Sign in to continue",
  helperText = "Access your workspace to upload artifacts, review extracted skills, and export a resume.",
  helperBullets = [
    "Upload projects (zip or repo)",
    "Review extracted skills",
    "Review a commit heatmap per project",
    "Export polished resume",
  ],
}) {
  return (
    <div className="min-h-screen bg-[#f6f8fc] text-slate-900">
      <header className="mx-auto max-w-6xl px-6 pt-6">
        <MainNav />
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-16 pt-10">
        {/* Centered layout */}
        <div className="mx-auto grid max-w-4xl gap-8 lg:grid-cols-[520px_1fr] lg:items-start">
          {/* Primary: form */}
          <section className="order-1">
            <div className="mb-5">
              {/* Small page context */}
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                {title}
              </p>
              {subtitle ? (
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  {subtitle}
                </p>
              ) : null}
            </div>

            {children}
          </section>

          {/* Secondary helper info */}
          <aside className="order-2 lg:pt-10">
            <div className="rounded-2xl bg-white/70 p-5 shadow-sm ring-1 ring-black/5">
              <p className="text-sm font-semibold text-slate-900">
                {helperTitle}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {helperText}
              </p>

              {/* Minimal bullets */}
              {helperBullets?.length ? (
                <ul className="mt-3 space-y-2 text-sm text-slate-600">
                  {helperBullets.map((b) => (
                    <li key={b} className="flex gap-2">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              ) : null}

              <div className="mt-4 h-px bg-slate-200/70" />
              <p className="mt-3 text-xs text-slate-500">
                Accounts are now connected to FastAPI authentication.
              </p>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
