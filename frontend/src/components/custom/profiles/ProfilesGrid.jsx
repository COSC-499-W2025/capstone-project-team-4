// src/components/custom/profiles/ProfilesGrid.jsx
import ProfileCard from "@/components/custom/profiles/ProfileCard";

export default function ProfilesGrid({ items }) {
    return (
        <div className="grid gap-6 md:grid-cols-2">
        {items.map((p) => (
            <ProfileCard key={p.id} profile={p} />
        ))}
        </div>
    );
}
