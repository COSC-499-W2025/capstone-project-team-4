import axios from "axios";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, User } from "lucide-react";

import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { clearAccessToken, getAccessToken } from "@/lib/auth";

function formatDate(value) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "N/A";
  return date.toLocaleString();
}

export default function AccountPage() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const authHeader = useMemo(() => {
    const token = getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : null;
  }, []);

  useEffect(() => {
    async function fetchCurrentUser() {
      setIsLoading(true);
      setError("");

      if (!authHeader) {
        setError("You are not signed in.");
        setIsLoading(false);
        return;
      }

      try {
        const response = await axios.get("/api/auth/me", {
          headers: authHeader,
        });
        setUser(response.data);
      } catch (err) {
        const status = err?.response?.status;
        const detail =
          err?.response?.data?.detail ||
          err?.message ||
          "Failed to load account.";

        if (status === 401) {
          clearAccessToken();
          setError("Session expired. Please log in again.");
        } else {
          setError(
            typeof detail === "string" ? detail : "Failed to load account.",
          );
        }
      } finally {
        setIsLoading(false);
      }
    }

    fetchCurrentUser();
  }, [authHeader]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <Navigation />

      <div className="mx-auto max-w-4xl px-4 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Account</h1>
          <p className="mt-2 text-sm text-slate-600">
            Logged-in account details. This page is the foundation for future
            profile and security settings.
          </p>
        </div>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-slate-900">
            <User className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Current User</h2>
          </div>

          {isLoading ? (
            <p className="text-sm text-slate-600">
              Loading account information...
            </p>
          ) : null}

          {!isLoading && error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <div className="flex items-center gap-2 font-medium">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            </div>
          ) : null}

          {!isLoading && !error && user ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Email
                </p>
                <p className="mt-1 text-sm font-medium text-slate-900">
                  {user.email}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  User ID
                </p>
                <p className="mt-1 text-sm font-medium text-slate-900">
                  {user.id}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Status
                </p>
                <p className="mt-1 flex items-center gap-2 text-sm font-medium text-emerald-700">
                  <CheckCircle2 className="h-4 w-4" />
                  {user.is_active ? "Active" : "Inactive"}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Created At
                </p>
                <p className="mt-1 text-sm font-medium text-slate-900">
                  {formatDate(user.created_at)}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 p-4 sm:col-span-2">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Last Updated
                </p>
                <p className="mt-1 text-sm font-medium text-slate-900">
                  {formatDate(user.updated_at)}
                </p>
              </div>
            </div>
          ) : null}
        </section>

        <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Account Settings (Coming Soon)
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            This section is intentionally prepared so profile edits can be added
            without changing page structure.
          </p>

          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-medium text-slate-900">Profile</p>
              <p className="mt-1 text-xs text-slate-600">
                Name, bio, links, and resume metadata.
              </p>
              <Button className="mt-3 w-full" variant="outline" disabled>
                Edit Profile
              </Button>
            </div>

            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-medium text-slate-900">Security</p>
              <p className="mt-1 text-xs text-slate-600">
                Password updates and login security controls.
              </p>
              <Button className="mt-3 w-full" variant="outline" disabled>
                Security Settings
              </Button>
            </div>

            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-medium text-slate-900">
                Data Controls
              </p>
              <p className="mt-1 text-xs text-slate-600">
                Privacy, export, and account deletion options.
              </p>
              <Button className="mt-3 w-full" variant="outline" disabled>
                Manage Data
              </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
