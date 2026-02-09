// src/components/custom/profiles/ProfilesHeader.jsx
export default function ProfilesHeader({ total, page, pages }) {
    return (
        <div className="mb-6 flex items-end justify-between">
        <div>
            <h2 className="text-xl font-semibold text-slate-900">Profiles</h2>
            <p className="text-sm text-slate-600 mt-1">
            Total: {total} • Page {page} of {pages}
            </p>
        </div>

        {/* placeholder for future filters/search */}
        <div className="text-sm text-slate-500">
            {/* e.g., Search / Sort later */}
        </div>
        </div>
    );
}
