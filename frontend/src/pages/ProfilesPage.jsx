// src/pages/ProfilesPage.jsx
import MainNav from "@/components/Navigation";
import EmptyProfilesState from "@/components/custom/profiles/EmptyProfilesState";
import ProfilesGrid from "@/components/custom/profiles/ProfilesGrid";
import ProfilesHeader from "@/components/custom/profiles/ProfilesHeader";
import ProfilesHero from "@/components/custom/profiles/ProfilesHero";
import { listProfiles } from "@/lib/user_profile_API";
import { useEffect, useState } from "react";

export default function ProfilesPage() {
    const [data, setData] = useState(null);
    const [err, setErr] = useState("");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        setErr("");

        listProfiles({ page: 1, page_size: 100 })
        .then((res) => setData(res))
        .catch((e) => setErr(e?.message ?? "Failed to load profiles"))
        .finally(() => setLoading(false));
    }, []);

    const items = data?.items ?? [];

    return (
        <>
        <MainNav />

        {/* Page shell */}
        <main className="bg-slate-50 min-h-[calc(100vh-64px)]">
            <div className="container mx-auto px-4">
            {/* Hero */}
            <ProfilesHero />
            
            {/* Content */}
            <section className="pb-16">
                {/* Sub-header row (pagination + totals) */}
                <div className="max-w-5xl mx-auto">
                <>
                <ProfilesHeader
                    total={data?.total ?? 0}
                    page={data?.page ?? 1}
                    pages={data?.pages ?? 1}
                />

                {items.length === 0 ? (
                    <EmptyProfilesState />
                ) : (
                    <ProfilesGrid items={items} />
                )}
                </>
                </div>
            </section>
            </div>
        </main>
        </>
    );
}
