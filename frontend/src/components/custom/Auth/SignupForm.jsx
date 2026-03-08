import axios from "axios";
import { Eye, EyeOff, Info } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import AuthCard from "@/components/custom/Auth/AuthCard";
import { usePasswordToggle } from "@/hooks/usePasswordToggle";

function isValidEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

export default function SignupForm() {
    const navigate = useNavigate();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");

    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");

    const [agree, setAgree] = useState(false);
    const [banner, setBanner] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const [touched, setTouched] = useState({
        name: false,
        email: false,
        password: false,
        confirm: false,
    });

    const pass = usePasswordToggle();
    const confirmPass = usePasswordToggle();

    const errors = useMemo(() => {
        const e = {};
        if (touched.name && name.trim().length < 2) e.name = "Enter your name.";
        if (touched.email && !isValidEmail(email)) e.email = "Enter a valid email.";
        if (touched.password && password.length < 8)
        e.password = "Password must be at least 8 characters.";
        if (touched.confirm && confirm !== password)
        e.confirm = "Passwords do not match.";
        return e;
    }, [name, email, password, confirm, touched]);

    const canSubmit = useMemo(() => {
        return (
        name.trim().length >= 2 &&
        isValidEmail(email) &&
        password.length >= 8 &&
        confirm === password &&
        agree
        );
    }, [name, email, password, confirm, agree]);

    async function onSubmit(e) {
        e.preventDefault();
        setBanner("");

        if (!canSubmit) {
        setTouched({ name: true, email: true, password: true, confirm: true });
        setBanner("Please fix the fields below.");
        return;
        }

        setIsSubmitting(true);
        try {
        await axios.post("/api/auth/register", {
            email,
            password,
        });

        navigate("/login", {
            replace: true,
            state: { email },
        });
        } catch (error) {
        const apiMessage =
            error?.response?.data?.detail ||
            error?.response?.data?.message ||
            error?.message ||
            "Signup failed.";
        setBanner(typeof apiMessage === "string" ? apiMessage : "Signup failed.");
        } finally {
        setIsSubmitting(false);
        }
    }

    return (
        <AuthCard
        heading="Sign up"
        subheading="Create an account to start building."
        >
        <Alert className="border-slate-200 bg-slate-50 text-slate-900">
            <AlertDescription className="flex gap-2 text-sm text-slate-700">
            <Info className="mt-0.5 h-4 w-4 text-slate-500" />
            <span>
                Create an account, then sign in to upload projects and generate resume output.
            </span>
            </AlertDescription>
        </Alert>

        {banner ? (
            <Alert className="border-slate-200 bg-white text-slate-900">
            <AlertDescription className="text-sm text-slate-700">
                {banner}
            </AlertDescription>
            </Alert>
        ) : null}

        <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
            <Label htmlFor="name" className="text-slate-700">
                Full name
            </Label>
            <Input
                id="name"
                placeholder="Your name"
                className="border-slate-200 bg-white focus-visible:ring-slate-400"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onBlur={() => setTouched((p) => ({ ...p, name: true }))}
                aria-invalid={Boolean(errors.name)}
            />
            {errors.name ? <p className="text-xs text-red-600">{errors.name}</p> : null}
            </div>

            <div className="space-y-2">
            <Label htmlFor="email" className="text-slate-700">
                Email
            </Label>
            <Input
                id="email"
                type="email"
                autoComplete="email"
                inputMode="email"
                placeholder="name@domain.com"
                className="border-slate-200 bg-white focus-visible:ring-slate-400"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => setTouched((p) => ({ ...p, email: true }))}
                aria-invalid={Boolean(errors.email)}
            />
            {errors.email ? (
                <p className="text-xs text-red-600">{errors.email}</p>
            ) : (
                <p className="text-xs text-slate-500">We’ll use this for exports and account access.</p>
            )}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-700">
                Password
                </Label>
                <div className="relative">
                <Input
                    id="password"
                    type={pass.inputType}
                    autoComplete="new-password"
                    placeholder="Min 8 characters"
                    className="border-slate-200 bg-white pr-11 focus-visible:ring-slate-400"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onBlur={() => setTouched((p) => ({ ...p, password: true }))}
                    aria-invalid={Boolean(errors.password)}
                />
                <button
                    type="button"
                    onClick={pass.toggle}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-2 text-slate-500 hover:text-slate-900"
                    aria-label={pass.show ? "Hide password" : "Show password"}
                >
                    {pass.show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
                </div>
                {errors.password ? (
                <p className="text-xs text-red-600">{errors.password}</p>
                ) : (
                <p className="text-xs text-slate-500">
                    Use a password you can remember—reset will come later.
                </p>
                )}
            </div>

            <div className="space-y-2">
                <Label htmlFor="confirm" className="text-slate-700">
                Confirm
                </Label>
                <div className="relative">
                <Input
                    id="confirm"
                    type={confirmPass.inputType}
                    autoComplete="new-password"
                    placeholder="Re-enter password"
                    className="border-slate-200 bg-white pr-11 focus-visible:ring-slate-400"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    onBlur={() => setTouched((p) => ({ ...p, confirm: true }))}
                    aria-invalid={Boolean(errors.confirm)}
                />
                <button
                    type="button"
                    onClick={confirmPass.toggle}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-2 text-slate-500 hover:text-slate-900"
                    aria-label={confirmPass.show ? "Hide password" : "Show password"}
                >
                    {confirmPass.show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
                </div>
                {errors.confirm ? (
                <p className="text-xs text-red-600">{errors.confirm}</p>
                ) : null}
            </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3">
            <Checkbox checked={agree} onCheckedChange={(v) => setAgree(Boolean(v))} />
            <div className="text-xs leading-relaxed text-slate-600">
                I agree to the <span className="text-slate-900">Terms</span> and{" "}
                <span className="text-slate-900">Privacy Policy</span>.
            </div>
            </div>

            <Button type="submit" className="w-full" disabled={!canSubmit || isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create account"}
            </Button>

            <p className="text-center text-sm text-slate-600">
            Already have an account?{" "}
            <Link
                to="/login"
                className="font-medium text-slate-900 underline underline-offset-4"
            >
                Sign in
            </Link>
            </p>
        </form>
        </AuthCard>
    );
}
