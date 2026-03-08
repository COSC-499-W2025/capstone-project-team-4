import axios from "axios";
import { Eye, EyeOff, Info } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import AuthCard from "@/components/custom/Auth/AuthCard";
import { usePasswordToggle } from "@/hooks/usePasswordToggle";
import { setAccessToken } from "@/lib/auth";

function isValidEmail(v) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

export default function LoginForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState(() => location?.state?.email || "");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [touched, setTouched] = useState({ email: false, password: false });
  const [banner, setBanner] = useState("");

  const { show, toggle, inputType } = usePasswordToggle();

  const errors = useMemo(() => {
    const e = {};
    if (touched.email && !isValidEmail(email)) e.email = "Enter a valid email.";
    if (touched.password && password.length < 1)
      e.password = "Password is required.";
    return e;
  }, [email, password, touched]);

  const canSubmit = useMemo(() => {
    return isValidEmail(email) && password.length > 0;
  }, [email, password]);

  async function onSubmit(e) {
    e.preventDefault();
    setBanner("");

    if (!canSubmit) {
      setTouched({ email: true, password: true });
      setBanner("Please fix the fields below.");
      return;
    }

    setIsSubmitting(true);

    try {
      // Backend uses OAuth2PasswordRequestForm (username/password form-encoded).
      const body = new URLSearchParams();
      body.set("username", email);
      body.set("password", password);

      const response = await axios.post("/api/auth/login", body, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      const token = response?.data?.access_token;
      if (!token) {
        setBanner("Login succeeded but token was not returned.");
        return;
      }

      setAccessToken(token);
      navigate("/generate", { replace: true });
    } catch (error) {
      const apiMessage =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Login failed.";
      setBanner(typeof apiMessage === "string" ? apiMessage : "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthCard
      heading="Log in"
      subheading="Use your email and password to continue."
    >
      {/* Friendly info banner */}
      <Alert className="border-slate-200 bg-slate-50 text-slate-900">
        <AlertDescription className="flex gap-2 text-sm text-slate-700">
          <Info className="mt-0.5 h-4 w-4 text-slate-500" />
          <span>Sign in with your registered email and password.</span>
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
            <p className="text-xs text-slate-500">
              Use the email you’ll attach to uploads and exports.
            </p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" className="text-slate-700">
              Password
            </Label>
            <button
              type="button"
              className="text-xs text-slate-500 hover:text-slate-900"
              onClick={() => setBanner("Reset not wired yet.")}
            >
              Forgot password?
            </button>
          </div>

          <div className="relative">
            <Input
              id="password"
              type={inputType}
              autoComplete="current-password"
              placeholder="Enter Password Here"
              className="border-slate-200 bg-white pr-11 focus-visible:ring-slate-400"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => setTouched((p) => ({ ...p, password: true }))}
              aria-invalid={Boolean(errors.password)}
            />
            <button
              type="button"
              onClick={toggle}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-2 text-slate-500 hover:text-slate-900"
              aria-label={show ? "Hide password" : "Show password"}
            >
              {show ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>

          {errors.password ? (
            <p className="text-xs text-red-600">{errors.password}</p>
          ) : null}
        </div>

        <Button
          type="submit"
          className="w-full"
          disabled={!canSubmit || isSubmitting}
        >
          {isSubmitting ? "Signing in..." : "Sign in"}
        </Button>

        <p className="text-center text-sm text-slate-600">
          New here?{" "}
          <Link
            to="/signup"
            className="font-medium text-slate-900 underline underline-offset-4"
          >
            Create an account
          </Link>
        </p>

        <p className="text-center text-xs text-slate-500">
          By continuing, you agree to our{" "}
          <span className="text-slate-800">Terms</span> and{" "}
          <span className="text-slate-800">Privacy Policy</span>.
        </p>
      </form>
    </AuthCard>
  );
}
