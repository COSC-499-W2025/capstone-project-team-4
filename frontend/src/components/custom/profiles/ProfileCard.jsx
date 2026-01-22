// src/components/custom/profiles/ProfileCard.jsx
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

function Initials({ first = "", last = "" }) {
    const a = (first?.[0] ?? "").toUpperCase();
    const b = (last?.[0] ?? "").toUpperCase();
    const text = (a + b) || "U";

    return (
        <div className="h-11 w-11 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center">
        <span className="text-sm font-semibold text-slate-700">{text}</span>
        </div>
    );
    }

export default function ProfileCard({ profile: p }) {
    const location = [p.city, p.state, p.country].filter(Boolean).join(", ");

    return (
        <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6 space-y-4">
            <div className="flex items-start gap-3">
            <Initials first={p.first_name} last={p.last_name} />

            <div className="min-w-0">
                <div className="text-lg font-semibold text-slate-900 truncate">
                {p.first_name} {p.last_name}
                </div>
                <div className="text-sm text-slate-600 truncate">{p.email}</div>
                {p.phone && <div className="text-sm text-slate-600">{p.phone}</div>}
                {location && <div className="text-sm text-slate-600">{location}</div>}
            </div>
            </div>

            {p.summary && (
            <p className="text-sm text-slate-600 leading-relaxed line-clamp-3">
                {p.summary}
            </p>
            )}

            <div className="flex gap-2 flex-wrap pt-1">
            {p.linkedin_url && (
                <Button variant="outline" size="sm" asChild className="border-slate-200">
                <a href={p.linkedin_url} target="_blank" rel="noreferrer">
                    LinkedIn
                </a>
                </Button>
            )}
            {p.github_url && (
                <Button variant="outline" size="sm" asChild className="border-slate-200">
                <a href={p.github_url} target="_blank" rel="noreferrer">
                    GitHub
                </a>
                </Button>
            )}
            {p.portfolio_url && (
                <Button variant="outline" size="sm" asChild className="border-slate-200">
                <a href={p.portfolio_url} target="_blank" rel="noreferrer">
                    Portfolio
                </a>
                </Button>
            )}
            </div>
        </CardContent>
        </Card>
    );
}
