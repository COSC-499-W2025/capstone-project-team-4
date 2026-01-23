import MainNav from "@/components/custom/Home/MainNav"
import Hero from "@/components/custom/Home/Hero"
import Steps from "@/components/custom/Home/Steps"
import CTA from "@/components/custom/Home/CTA"
import FeaturesSection from "@/components/custom/Home/FeaturesSection"

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