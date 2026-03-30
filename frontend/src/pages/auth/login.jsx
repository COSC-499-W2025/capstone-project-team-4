import AuthShell from "@/components/custom/Auth/AuthShell";
import LoginForm from "@/components/custom/Auth/LoginForm";

export default function LoginPage() {
  return (
    <AuthShell
      title="Coding Project Analyzer"
      subtitle="Upload project files and generate a comprehensive summary of your project."
    >
      <LoginForm />
    </AuthShell>
  );
}
