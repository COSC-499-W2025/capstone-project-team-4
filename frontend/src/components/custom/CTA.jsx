import { Button } from "@/components/ui/button"
export default function CTA() {
  return (
      <section className="container mx-auto px-4 py-16 mb-16">
        <div className="max-w-4xl mx-auto bg-slate-900 rounded-2xl p-8 md:p-12 text-center text-white">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Create Your Resume?
          </h2>
          <p className="text-lg text-slate-300 mb-8">
            Transform your work history into a professional resume that highlights your best contributions.
          </p>
          <Button size="lg" variant="secondary" className="text-lg px-8">
            Start Building Now
          </Button>
        </div>
      </section>
    )
}