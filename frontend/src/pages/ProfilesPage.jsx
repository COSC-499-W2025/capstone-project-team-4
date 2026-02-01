// src/pages/ProfilesPage.jsx
import MainNav from "@/components/Navigation";
import EmptyProfilesState from "@/components/custom/profiles/EmptyProfilesState";
import ProfileDialog from "@/components/custom/profiles/ProfileDialog";
import ProfilesGrid from "@/components/custom/profiles/ProfilesGrid";
import ProfilesHeader from "@/components/custom/profiles/ProfilesHeader";
import ProfilesHero from "@/components/custom/profiles/ProfilesHero";
import { listProfiles } from "@/lib/user_profile_API";
import { useCallback, useEffect, useState } from "react";

export default function ProfilesPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const refresh = useCallback(async () => {
  console.log("refresh() called");
  setLoading(true);
  setErr("");
  try {
    const res = await listProfiles({ page: 1, page_size: 100 });
    console.log("refresh() got:", res);
    setData(res);
  } catch (e) {
    console.error("refresh() error:", e);
    setErr(e?.message ?? "Failed to load profiles");
  } finally {
    setLoading(false);
  }
}, []);
  useEffect(() => {
    refresh();
  }, [refresh]);
  const openCreate = useCallback(() => {
    setEditingUserId(null);
    setDialogOpen(true);
  }, []);
  const openEdit = useCallback((profile) => {
    setEditingUserId(profile.user_id);
    setDialogOpen(true);
  }, []);
  const items = data?.items ?? [];

  return (
    <>
      <MainNav />
      <ProfileDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        initialUserId={editingUserId}
        onSaved={refresh}
      />
      <main className="bg-slate-50 min-h-[calc(100vh-64px)]">
        <div className="container mx-auto px-4">
          <ProfilesHero onCreateProfile={openCreate} onRefresh={refresh} />
          <section className="pb-16">
            <div className="max-w-5xl mx-auto">
              <ProfilesHeader
                total={data?.total ?? 0}
                page={data?.page ?? 1}
                pages={data?.pages ?? 1}
              />
              {err && (
                <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {err}
                </div>
              )}
              {items.length === 0 ? (
                <EmptyProfilesState onCreateProfile={openCreate} onRefresh={refresh} />
              ) : (
                <ProfilesGrid items={items} onEdit={openEdit} />
              )}
            </div>
          </section>
        </div>
      </main>
    </>
  );
}
