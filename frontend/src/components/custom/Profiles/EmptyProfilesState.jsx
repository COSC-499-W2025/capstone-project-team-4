// src/components/custom/profiles/EmptyProfilesState.jsx
import { Card, CardContent } from "@/components/ui/card";

export default function EmptyProfilesState() {
    return (
        <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-8">
            <div className="text-lg font-semibold text-slate-900">No profiles yet</div>
            <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            Create profiles to view here.
            </p>
            <div className="mt-6 flex gap-3">
            <button
                disabled
                className="h-10 px-5 rounded-md bg-slate-900 text-white text-sm font-medium opacity-60 cursor-not-allowed"
                title="Create Profile (coming soon)"
            >
                Create Profile
            </button>
            <button
                className="h-10 px-5 rounded-md bg-white text-slate-900 text-sm font-medium border border-slate-200 shadow-sm hover:bg-slate-50 transition"
                onClick={() => window.location.reload()}
            >
                Refresh
            </button>
            </div>
        </CardContent>
        </Card>
    );
}
