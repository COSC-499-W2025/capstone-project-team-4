import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function Steps() {
  return (
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12 text-slate-900">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <Card className="border-2 hover:border-slate-300 transition-colors">
            <CardHeader>
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4 mx-auto">
                <span className="text-2xl font-bold text-blue-600">1</span>
              </div>
              <CardTitle className="text-center">Upload Your Projects</CardTitle>
              <CardDescription className="text-base text-center">
                Upload zip files containing your project folders - code repositories, documents, designs, and more. Our system analyzes your work artifacts to understand your contributions.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-2 hover:border-slate-300 transition-colors">
            <CardHeader>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4 mx-auto">
                <span className="text-2xl font-bold text-green-600">2</span>
              </div>
              <CardTitle className="text-center">Review & Customize</CardTitle>
              <CardDescription className="text-base text-center">
                Our intelligent system extracts your skills, contributions, and project metrics. Review the insights, customize the details, and select what to highlight.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-2 hover:border-slate-300 transition-colors">
            <CardHeader>
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4 mx-auto">
                <span className="text-2xl font-bold text-purple-600">3</span>
              </div>
              <CardTitle className="text-center">Generate Your Resume</CardTitle>
              <CardDescription className="text-base text-center">
                Click "Start Building Now" to generate your professional resume.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>
  )
} 