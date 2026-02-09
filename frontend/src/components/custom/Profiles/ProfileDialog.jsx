import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  createProfile,
  getProfileByUserId,
  updateProfile,
} from "@/lib/user_profile_API";
import { AlertCircle, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

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

const cn = (...a) => a.filter(Boolean).join(" ");

const normalizePhone = (raw) => String(raw ?? "").replace(/\D/g, "").slice(0, 15);
const nonEmpty = (s) => String(s ?? "").trim().length > 0;

const validUrlIfProvided = (s) => {
  const v = String(s ?? "").trim();
  if (!v) return true;
  try {
    const u = new URL(v);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
};

const validPhoneIfProvided = (digits) => {
  const v = String(digits ?? "").trim();
  if (!v) return true;
  return v.length >= 10 && v.length <= 15;
};

const pickEditableFields = (data) => {
  const d = data || {};
  return {
    first_name: d.first_name ?? "",
    last_name: d.last_name ?? "",
    phone: normalizePhone(d.phone ?? ""),
    city: d.city ?? "",
    state: d.state ?? "",
    country: d.country ?? "",
    linkedin_url: d.linkedin_url ?? "",
    github_url: d.github_url ?? "",
    portfolio_url: d.portfolio_url ?? "",
    summary: d.summary ?? "",
  };
};

export default function ProfileDialog({
  open,
  onOpenChange,
  initialUserId = null,
  onSaved,
}) {
  const [userIdInput, setUserIdInput] = useState(
    initialUserId ? String(initialUserId) : ""
  );
  const [form, setForm] = useState(EMPTY_PROFILE);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [saving, setSaving] = useState(false);
  const [mode, setMode] = useState("create");
  const [err, setErr] = useState("");
  const [touched, setTouched] = useState({});

  const busy = loadingProfile || saving;
  const touch = (k) => setTouched((p) => ({ ...p, [k]: true }));

  const userId = useMemo(() => {
    const n = Number(userIdInput);
    return Number.isFinite(n) && n > 0 ? n : null;
  }, [userIdInput]);

  const v = useMemo(() => {
    const firstNameOk = nonEmpty(form.first_name);
    const lastNameOk = nonEmpty(form.last_name);
    const phoneOk = validPhoneIfProvided(form.phone);
    const linkedinOk = validUrlIfProvided(form.linkedin_url);
    const githubOk = validUrlIfProvided(form.github_url);
    const portfolioOk = validUrlIfProvided(form.portfolio_url);
    const isValidUserId = !!userId;
    const formOk =
      isValidUserId &&
      firstNameOk &&
      lastNameOk &&
      phoneOk &&
      linkedinOk &&
      githubOk &&
      portfolioOk;

    return {
      firstNameOk,
      lastNameOk,
      phoneOk,
      linkedinOk,
      githubOk,
      portfolioOk,
      isValidUserId,
      formOk,
    };
  }, [form, userId]);

  useEffect(() => {
    if (!open) return;

    setErr("");
    setLoadingProfile(false);
    setSaving(false);
    setForm(EMPTY_PROFILE);
    setMode("create");
    setTouched({});
    setUserIdInput(initialUserId ? String(initialUserId) : "");

    if (initialUserId) loadExistingWithId(Number(initialUserId));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initialUserId]);

  async function loadExistingWithId(id) {
    setErr("");
    if (!id || id <= 0) {
      setErr("Enter a valid user id first.");
      return;
    }

    setLoadingProfile(true);
    try {
      const data = await getProfileByUserId(id);
      setForm(pickEditableFields(data));
      setMode("update");
    } catch (e) {
      if (e?.status === 404) {
        setForm(EMPTY_PROFILE);
        setMode("create");
        setErr("No profile found for this user. Fill fields to create one.");
      } else {
        setErr(e?.message ?? "Failed to load profile");
      }
    } finally {
      setLoadingProfile(false);
    }
  }

  async function loadExisting() {
    if (!userId) {
      touch("user_id");
      setErr("Enter a valid user id first.");
      return;
    }
    return loadExistingWithId(userId);
  }

  async function save() {
    setErr("");

    if (loadingProfile) {
      setErr("Please wait for the profile to finish loading.");
      return;
    }

    if (!userId) {
      touch("user_id");
      setErr("Enter a valid user id first.");
      return;
    }

    setSaving(true);
    try {
      if (mode === "update") await updateProfile(userId, form);
      else await createProfile(userId, form);

      onOpenChange(false);
      onSaved?.();
    } catch (e) {
      setErr(e?.message ?? "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  const setField = (field) => (e) => {
    const val = e.target.value;
    setForm((p) => ({
      ...p,
      [field]: field === "phone" ? normalizePhone(val) : val,
    }));
  };

  function attemptSubmit() {
    [
      "user_id",
      "first_name",
      "last_name",
      "phone",
      "linkedin_url",
      "github_url",
      "portfolio_url",
    ].forEach(touch);

    if (loadingProfile) {
      setErr("Please wait for the profile to finish loading.");
      return;
    }

    if (!v.formOk) return;
    save();
  }

  const userIdState =
    userIdInput.trim().length === 0 ? "neutral" : v.isValidUserId ? "valid" : "invalid";

  const userIdClass = cn(
    "h-11",
    userIdState === "valid" && "border-emerald-500 focus-visible:ring-emerald-500/30",
    userIdState === "invalid" &&
      "border-destructive focus-visible:ring-destructive/30"
  );

  const userIdInvalid =
    (touched.user_id && !v.isValidUserId) || userIdState === "invalid";

  const urlFields = [
    {
      key: "linkedin_url",
      label: "LinkedIn URL",
      placeholder: "https://www.linkedin.com/in/your-handle",
      ok: v.linkedinOk,
    },
    {
      key: "github_url",
      label: "GitHub URL",
      placeholder: "https://github.com/your-username",
      ok: v.githubOk,
    },
    {
      key: "portfolio_url",
      label: "Portfolio URL",
      placeholder: "https://yourdomain.com",
      ok: v.portfolioOk,
    },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="p-0 w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        <DialogTop
          title={mode === "update" ? "Update Profile" : "Create Profile"}
          description={
            <>
              Load an existing profile by User ID, then edit and save.
              <span className="ml-1 text-muted-foreground">(Auth later → auto-fill.)</span>
            </>
          }
        />

        <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-5 space-y-5">
          {err ? <ErrorBanner message={err} /> : null}

          <div className="rounded-xl border bg-muted/30 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex-1">
                <Label label="User ID" required />
                <Input
                  value={userIdInput}
                  onChange={(e) => setUserIdInput(e.target.value)}
                  onBlur={() => touch("user_id")}
                  placeholder="1"
                  inputMode="numeric"
                  disabled={busy}
                  className={cn(
                    userIdClass,
                    touched.user_id && userIdState === "neutral"
                      ? "border-destructive focus-visible:ring-destructive/30"
                      : ""
                  )}
                  aria-invalid={userIdInvalid ? "true" : "false"}
                />
              </div>

              <div className="sm:w-40">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={loadExisting}
                  disabled={loadingProfile || saving || !v.isValidUserId}
                  className="h-11 w-full"
                >
                  {loadingProfile ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Loading
                    </>
                  ) : (
                    "Load profile"
                  )}
                </Button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <InputField
              label="First name"
              required
              value={form.first_name}
              placeholder="John"
              autoComplete="given-name"
              disabled={busy}
              touched={!!touched.first_name}
              ok={v.firstNameOk}
              onBlur={() => touch("first_name")}
              onChange={setField("first_name")}
            />

            <InputField
              label="Last name"
              required
              value={form.last_name}
              placeholder="Doe"
              autoComplete="family-name"
              disabled={busy}
              touched={!!touched.last_name}
              ok={v.lastNameOk}
              onBlur={() => touch("last_name")}
              onChange={setField("last_name")}
            />

            <InputField
              label="Phone"
              value={form.phone}
              placeholder="2505550123"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              pattern="^\\d{10,15}$"
              disabled={busy}
              touched={!!touched.phone}
              ok={v.phoneOk}
              onBlur={() => touch("phone")}
              onChange={setField("phone")}
            />

            <InputField
              label="City"
              value={form.city}
              placeholder="Kelowna"
              autoComplete="address-level2"
              disabled={busy}
              onChange={setField("city")}
            />

            <InputField
              label="State / Province"
              value={form.state}
              placeholder="British Columbia"
              autoComplete="address-level1"
              disabled={busy}
              onChange={setField("state")}
            />

            <InputField
              label="Country"
              value={form.country}
              placeholder="Canada"
              autoComplete="country-name"
              disabled={busy}
              onChange={setField("country")}
            />

            <div className="md:col-span-2">
              <div className="rounded-xl border bg-background p-4">
                <div className="mb-3 text-sm font-semibold text-foreground">
                  Links
                  <span className="ml-2 text-xs font-normal text-muted-foreground">
                    (optional)
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  {urlFields.map((f) => (
                    <InputField
                      key={f.key}
                      label={f.label}
                      value={form[f.key]}
                      placeholder={f.placeholder}
                      type="url"
                      inputMode="url"
                      autoComplete="url"
                      disabled={busy}
                      touched={!!touched[f.key]}
                      ok={f.ok}
                      onBlur={() => touch(f.key)}
                      onChange={setField(f.key)}
                    />
                  ))}
                </div>
              </div>
            </div>

            <Field label="Summary" className="md:col-span-2">
              <Textarea
                rows={6}
                value={form.summary}
                onChange={setField("summary")}
                placeholder="Full-stack developer focused on building clean, data-driven products…"
                className="min-h-[140px] resize-y"
                disabled={busy}
              />
            </Field>
          </div>
        </div>

        <DialogActions
          loading={busy}
          mode={mode}
          canSubmit={v.formOk}
          onCancel={() => onOpenChange(false)}
          onSubmit={attemptSubmit}
        />
      </DialogContent>
    </Dialog>
  );
}

function DialogTop({ title, description }) {
  return (
    <div className="border-b bg-background px-4 sm:px-6 py-4 sm:py-5">
      <DialogHeader className="space-y-1">
        <DialogTitle className="text-xl">{title}</DialogTitle>
        <DialogDescription className="text-sm">{description}</DialogDescription>
      </DialogHeader>
    </div>
  );
}

function ErrorBanner({ message }) {
  return (
    <div className="flex gap-3 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
      <AlertCircle className="h-4 w-4 mt-0.5" />
      <div className="leading-relaxed">{message}</div>
    </div>
  );
}

function DialogActions({ loading, mode, canSubmit, onCancel, onSubmit }) {
  return (
    <div className="sticky bottom-0 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/75 px-4 sm:px-6 py-4">
      <DialogFooter className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end sm:gap-3">
        <Button variant="ghost" onClick={onCancel} disabled={loading} className="h-11">
          Cancel
        </Button>

        <Button onClick={onSubmit} disabled={loading || !canSubmit} className="h-11">
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving
            </>
          ) : mode === "update" ? (
            "Save changes"
          ) : (
            "Create profile"
          )}
        </Button>
      </DialogFooter>
    </div>
  );
}

function Label({ label, required = false }) {
  return (
    <div className="mb-1.5 text-sm font-medium text-foreground">
      {label}
      {required ? <span className="ml-1 text-destructive">*</span> : null}
    </div>
  );
}

function Field({ label, children, className = "", required = false }) {
  return (
    <div className={className}>
      <Label label={label} required={required} />
      {children}
    </div>
  );
}

function InputField({
  label,
  required = false,
  value,
  onChange,
  onBlur,
  placeholder,
  autoComplete,
  type,
  inputMode,
  pattern,
  disabled,
  touched,
  ok,
}) {
  const showError = touched && ok === false;
  return (
    <Field label={label} required={required}>
      <Input
        className={cn(
          "h-11",
          showError && "border-destructive focus-visible:ring-destructive/30"
        )}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={placeholder}
        autoComplete={autoComplete}
        type={type}
        inputMode={inputMode}
        pattern={pattern}
        disabled={disabled}
        aria-invalid={showError ? "true" : "false"}
        required={required}
      />
    </Field>
  );
}
