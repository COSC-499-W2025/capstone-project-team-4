import { Button } from "@/components/ui/button";

export default function Hero() {
  return (
    <section className="container mx-auto px-4 py-16 md:py-24">
      <div className="max-w-3xl mx-auto text-center space-y-6">
        <h1 className="text-4xl md:text-6xl font-bold text-slate-900 tracking-tight">
          Resume Builder
        </h1>
        <p className="text-xl text-slate-600 leading-relaxed">
          Upload your project files, and our system will analyze your contributions, skills, and project metrics to generate a polished resume that showcases your best work.
        </p>
        <div className="flex gap-4 justify-center pt-4">
          <Button size="lg" className="text-lg px-8">
            Get Started
          </Button>
          <Button size="lg" variant="outline" className="text-lg px-8">
            View Examples
          </Button>
        </div>
      </div>
    </section>
  );
}