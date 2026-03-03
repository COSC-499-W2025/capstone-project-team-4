// src/components/custom/Profiles/ProfilesHero.jsx
export default function ProfilesHero({ onCreateProfile, onRefresh }) {
    return (
        <section className="container mx-auto px-4 py-16 md:py-24">
        <div className="max-w-3xl mx-auto text-center space-y-6">
            <h1 className="text-4xl md:text-6xl font-bold text-slate-900 tracking-tight">
            User Profiles
            </h1>
            <p className="text-xl text-slate-350 leading-relaxed">
            Manage professional identited and view consolidated summaries of analyzed projects.
            </p>
            <p>Admin-View</p>
            <div className="pt-2 flex justify-center gap-3">
            <button
                className="h-10 px-5 rounded-md bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 transition"
                onClick={onCreateProfile}
            >
                Create Profile
            </button>
            <button
                className="h-10 px-5 rounded-md bg-white text-slate-900 text-sm font-medium border border-slate-200 shadow-sm hover:bg-slate-50 transition"
                onClick={onRefresh}
            >
                Refresh
            </button>
            </div>
            <div className="text-xs text-slate-500">
            User ID is required for now and will be auto-filled once authentication is added.
            </div>
        </div>
        </section>
    );
}