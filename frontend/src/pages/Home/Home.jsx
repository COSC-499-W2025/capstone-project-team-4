import MainNav from "@/components/custom/MainNav"
import Hero from "@/components/custom/Hero"
import Steps from "@/components/custom/Steps"
import CTA from "@/components/custom/CTA"
import FeaturesSection from "@/components/custom/FeaturesSection"

export default function MainPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <MainNav />
      <Hero />
      <Steps />
      <CTA />
      <FeaturesSection />
    </div>
  )
}