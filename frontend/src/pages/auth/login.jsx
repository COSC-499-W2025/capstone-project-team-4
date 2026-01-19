import AuthShell from "@/components/custom/Auth/AuthShell";
import LoginForm from "@/components/custom/Auth/LoginForm";

export default function LoginPage() {
  return (
    <AuthShell
      title="Resume Builder"
      subtitle="Upload project files and generate a polished resume with skills and contributions extracted from real artifacts."
    >
      <LoginForm />
    </AuthShell>
  );
}
