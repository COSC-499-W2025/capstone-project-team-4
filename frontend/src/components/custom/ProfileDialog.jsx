import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import {
    Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

import { getMyProfile, upsertMyProfile } from "@/lib/userProfileApi";

const EMPTY_PROFILE = {
    first_name: "",
    last_name: "",
    phone: "",
    city: "",
    state: "",
    country: "",
    linkedin_url: "",
    github_url: "",
    portfolio_url: "",
    summary: "",
};

function pickEditableFields(data) {
    return {
        first_name: data?.first_name ?? "",
        last_name: data?.last_name ?? "",
        phone: data?.phone ?? "",
        city: data?.city ?? "",
        state: data?.state ?? "",
        country: data?.country ?? "",
        linkedin_url: data?.linkedin_url ?? "",
        github_url: data?.github_url ?? "",
        portfolio_url: data?.portfolio_url ?? "",
        summary: data?.summary ?? "",
    };
}

export default function ProfileDialog({ open, onOpenChange }) {
    const [form, setForm] = useState(EMPTY_PROFILE);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!open) return;

        setError("");
        setSaving(false);
        setForm(EMPTY_PROFILE);
        loadProfile();
    }, [open]);

    async function loadProfile() {
        setLoading(true);
        setError("");

        try {
            const data = await getMyProfile();
            setForm(pickEditableFields(data));
        } catch (err) {
            if (err.status === 404) {
                setForm(EMPTY_PROFILE);
            } else {
                setError("Failed to load profile.");
            }
        } finally {
            setLoading(false);
        }
    }

    function updateField(field, value) {
        setForm((prev) => ({
            ...prev,
            [field]: value,
        }));
    }

    async function handleSave() {
        setError("");

        if (!form.first_name.trim() || !form.last_name.trim()) {
            setError("First name and last name are required.");
            return;
        }

        setSaving(true);

        try {
            await upsertMyProfile(form);
            onOpenChange(false);
        } catch {
            setError("Failed to save profile.");
        } finally {
            setSaving(false);
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>Edit Profile</DialogTitle>
                </DialogHeader>

                {loading ? (
                    <div className="flex justify-center py-10">
                        <Loader2 className="h-5 w-5 animate-spin" />
                    </div>
                ) : (
                    <div className="grid gap-4">
                        <label className="text-sm font-medium">
                            First Name <span className="text-red-500">*</span>
                        </label>
                        {error && <div className="text-sm text-red-600">{error}</div>}
                        <Input
                            required
                            placeholder="First Name"
                            value={form.first_name}
                            onChange={(e) => updateField("first_name", e.target.value)}
                        />
                        <label className="text-sm font-medium">
                            Last Name <span className="text-red-500">*</span>
                        </label>
                        <Input
                            required
                            placeholder="Last Name"
                            value={form.last_name}
                            onChange={(e) => updateField("last_name", e.target.value)}
                        />
                        <Input
                            placeholder="Phone"
                            value={form.phone}
                            onChange={(e) => updateField("phone", e.target.value)}
                        />
                        <Input
                            placeholder="Country"
                            value={form.country}
                            onChange={(e) => updateField("country", e.target.value)}
                        />
                        <Input
                            placeholder="State / Province"
                            value={form.state}
                            onChange={(e) => updateField("state", e.target.value)}
                        />
                        <Input
                            placeholder="City"
                            value={form.city}
                            onChange={(e) => updateField("city", e.target.value)}
                        />
                        <Input
                            placeholder="LinkedIn URL"
                            value={form.linkedin_url}
                            onChange={(e) => updateField("linkedin_url", e.target.value)}
                        />
                        <Input
                            placeholder="GitHub URL"
                            value={form.github_url}
                            onChange={(e) => updateField("github_url", e.target.value)}
                        />
                        <Input
                            placeholder="Portfolio URL"
                            value={form.portfolio_url}
                            onChange={(e) => updateField("portfolio_url", e.target.value)}
                        />
                        <Textarea
                            placeholder="Summary"
                            value={form.summary}
                            onChange={(e) => updateField("summary", e.target.value)}
                        />
                    </div>
                )}

                <DialogFooter>
                    <Button
                        variant="ghost"
                        onClick={() => onOpenChange(false)}
                        disabled={saving}
                    >
                        Cancel
                    </Button>

                    <Button onClick={handleSave} disabled={saving || loading}>
                        {saving ? "Saving..." : "Save Profile"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}