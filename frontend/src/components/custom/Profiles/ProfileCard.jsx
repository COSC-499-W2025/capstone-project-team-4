import { Card, CardContent } from "@/components/ui/card";

function Initials({ first = "", last = "" }) {
  const a = (first?.[0] ?? "").toUpperCase();
  const b = (last?.[0] ?? "").toUpperCase();
  const text = (a + b) || "U";

  return (
    <div className="h-12 w-12 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center shadow-sm">
      <span className="text-sm font-semibold text-slate-700">{text}</span>
    </div>
  );
}
function FieldRow({ label, value }) {
  const missing = !value;
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div
        className={
          "text-sm text-right break-all " +
          (missing ? "text-slate-400 italic" : "text-slate-700")
        }
      >
        {missing ? "Missing" : value}
      </div>
    </div>
  );
}

export default function ProfileCard({ profile: p, onClick }) {
  const location = [p.city, p.state, p.country].filter(Boolean).join(", ");
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => (e.key === "Enter" ? onClick?.() : null)}
      className="cursor-pointer rounded-xl transition focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2 focus:ring-offset-white"
    >
      <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow rounded-xl h-full">
        <CardContent className="p-6 h-full">
          <div className="flex flex-col items-center text-center gap-4 h-full">
            <Initials first={p.first_name} last={p.last_name} />
            <div className="min-w-0 w-full">
              <div className="text-lg font-semibold text-slate-900 truncate">
                {[p.first_name, p.last_name].filter(Boolean).join(" ") || "Missing"}
              </div>
              <div className="text-sm text-slate-600 truncate">
                {p.email || <span className="text-slate-400 italic">Missing</span>}
              </div>
            </div>
            <div className="w-full rounded-lg border border-slate-200 bg-slate-50/60 p-4 text-left space-y-2">
              <FieldRow label="Phone" value={p.phone} />
              <FieldRow label="Location" value={location} />
              <FieldRow label="LinkedIn" value={p.linkedin_url} />
              <FieldRow label="GitHub" value={p.github_url} />
              <FieldRow label="Portfolio" value={p.portfolio_url} />
            </div>
            <div className="w-full">
              <div className="text-xs font-medium text-slate-500 mb-1">Summary</div>
              <div className="min-h-[3.75rem] text-sm text-slate-600 leading-relaxed">
                {p.summary ? (
                  <p className="line-clamp-3">{p.summary}</p>
                ) : (
                  <span className="text-slate-400 italic">Missing</span>
                )}
              </div>
            </div>
            <div className="mt-auto w-full pt-2">
              <div className="h-px w-full bg-slate-200" />
              <div className="mt-3 text-xs text-slate-500">
                Click to view or edit profile
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
