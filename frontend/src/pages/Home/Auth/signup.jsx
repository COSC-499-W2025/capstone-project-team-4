import AuthShell from "@/components/custom/Auth/AuthShell";
import SignupForm from "@/components/custom/Auth/SignupForm";

export default function SignupPage() {
    return (
        <AuthShell
        title="Create your account"
        subtitle="Set up your workspace to upload projects, review extracted insights, and export a professional resume."
        >
        <SignupForm />
        </AuthShell>
    );
}
