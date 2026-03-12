import React, { useCallback, useRef, useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Download, FileText } from 'lucide-react';
import Navigation from '@/components/Navigation';
import PersonalInfoForm from '@/components/custom/ResumeBuilder/PersonalInfoForm';
import EducationForm from '@/components/custom/ResumeBuilder/EducationForm';
import ExperienceForm from '@/components/custom/ResumeBuilder/ExperienceForm';
import ProjectsForm from '@/components/custom/ResumeBuilder/ProjectsForm';
import SkillsForm from '@/components/custom/ResumeBuilder/SkillsForm';
import ResumePreview from '@/components/custom/ResumeBuilder/ResumePreview';
import { exportResume } from '@/components/custom/ResumeBuilder/exportResume';

const INITIAL_STATE = {
  contact: { name: '', phone: '', email: '', linkedin_url: '', github_url: '', portfolio_url: '', location: '' },
  summary: '',
  education: [{ id: crypto.randomUUID(), institution: '', degree: '', field_of_study: '', start_date: '', end_date: '', is_current: false, location: '', gpa: '' }],
  experience: [{ id: crypto.randomUUID(), company_name: '', job_title: '', location: '', is_remote: false, start_date: '', end_date: '', is_current: false, responsibilities: [], achievements: [] }],
  projects: [{ id: crypto.randomUUID(), title: '', technologies: [], date_label: '', highlights: [] }],
  skills: [{ id: crypto.randomUUID(), category: '', skills: [] }],
};

const TABS = [
  { value: 'personal', label: 'Personal Info' },
  { value: 'education', label: 'Education' },
  { value: 'experience', label: 'Experience' },
  { value: 'projects', label: 'Projects' },
  { value: 'skills', label: 'Skills' },
];

function SectionWrapper({ title, description, children }) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-semibold">{title}</h2>
        {description && <p className="text-sm text-muted-foreground mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  );
}

/**
 * Converts a "YYYY-MM" month-input string to a full date "YYYY-MM-01".
 * Returns null for empty/missing values.
 */
function toDate(s) {
  return s ? `${s}-01` : null;
}

/**
 * Transforms internal form state to the FullResumeData API schema shape:
 * - Strips frontend-only `id` fields
 * - Converts "YYYY-MM" month strings to "YYYY-MM-01" date strings
 * - Filters out incomplete entries (no institution / company_name / title / category)
 * - Converts skills array to Dict<string, string[]>
 * - Adds generated_at timestamp
 */
function toAPIData(data) {
  return {
    contact: data.contact,
    summary: data.summary || null,
    education: data.education
      .filter(e => e.institution)
      .map(({ id: _id, ...e }) => ({ ...e, start_date: toDate(e.start_date), end_date: toDate(e.end_date) })),
    experience: data.experience
      .filter(e => e.company_name)
      .map(({ id: _id, ...e }) => ({ ...e, start_date: toDate(e.start_date), end_date: toDate(e.end_date) })),
    projects: data.projects
      .filter(p => p.title)
      .map(({ id: _id, ...p }) => p),
    skills: Object.fromEntries(
      data.skills
        .filter(s => s.category && s.skills.length)
        .map(({ id: _id, ...s }) => [s.category, s.skills])
    ),
    generated_at: new Date().toISOString(),
  };
}

// 8.5in at 96 dpi
const IFRAME_WIDTH_PX = 816;
const IFRAME_HEIGHT_PX = Math.round(IFRAME_WIDTH_PX * 11 / 8.5); // 1056px
// margin on each side in px
const PREVIEW_MARGIN_PX = 16;

export default function ResumeBuilder() {
  const [data, setData] = useState(INITIAL_STATE);
  const [showPreview, setShowPreview] = useState(true);
  const [previewScale, setPreviewScale] = useState(0.75);
  const [exporting, setExporting] = useState(false);
  const observerRef = useRef(null);

  const handleExport = async (format) => {
    setExporting(true);
    try {
      await exportResume(toAPIData(data), format);
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  // Callback ref — re-runs whenever the preview panel mounts or unmounts
  const previewPanelRef = useCallback((el) => {
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      const available = entry.contentRect.width - PREVIEW_MARGIN_PX * 2;
      setPreviewScale(Math.min(1, available / IFRAME_WIDTH_PX));
    });
    observer.observe(el);
    observerRef.current = observer;
  }, []);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navigation />

      {/* Sub-header */}
      <div className="border-b bg-background">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-primary" />
            <div>
              <h1 className="text-lg font-semibold leading-none">Resume Builder</h1>
              <p className="text-xs text-muted-foreground mt-0.5">Jake&apos;s Resume format &mdash; ATS friendly</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowPreview(v => !v)}
              className="hidden lg:flex"
            >
              {showPreview ? 'Hide Preview' : 'Show Preview'}
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button size="sm" className="gap-2" disabled={exporting}>
                  <Download className="h-4 w-4" />
                  {exporting ? 'Exporting…' : 'Export'}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleExport('html')}>
                  HTML (.html)
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('pdf')}>
                  PDF (.pdf)
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('markdown')}>
                  Markdown (.md)
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Two-column layout — form takes full width when preview is hidden */}
      <div className={`flex-1 overflow-hidden ${showPreview ? 'lg:grid lg:grid-cols-[480px_1fr]' : 'flex'}`}>

        {/* Form panel */}
        <div className={`overflow-y-auto ${showPreview ? 'border-r' : 'w-full'}`}>
          <div className={`p-5 ${showPreview ? '' : 'max-w-3xl mx-auto'}`}>
            <Tabs defaultValue="personal">
              <TabsList className="w-full flex-wrap h-auto gap-1 mb-5 bg-muted/50 p-1">
                {TABS.map(tab => (
                  <TabsTrigger key={tab.value} value={tab.value} className="flex-1 text-xs">
                    {tab.label}
                  </TabsTrigger>
                ))}
              </TabsList>

              <TabsContent value="personal">
                <SectionWrapper title="Personal Information" description="Your contact details and a brief professional summary.">
                  <PersonalInfoForm
                    contact={data.contact}
                    summary={data.summary}
                    onContactChange={contact => setData(d => ({ ...d, contact }))}
                    onSummaryChange={summary => setData(d => ({ ...d, summary }))}
                  />
                </SectionWrapper>
              </TabsContent>

              <TabsContent value="education">
                <SectionWrapper title="Education" description="Your academic background, most recent first.">
                  <EducationForm entries={data.education} onChange={education => setData(d => ({ ...d, education }))} />
                </SectionWrapper>
              </TabsContent>

              <TabsContent value="experience">
                <SectionWrapper title="Work Experience" description="Your professional experience, most recent first.">
                  <ExperienceForm entries={data.experience} onChange={experience => setData(d => ({ ...d, experience }))} />
                </SectionWrapper>
              </TabsContent>

              <TabsContent value="projects">
                <SectionWrapper title="Projects" description="Noteworthy projects with technologies and highlights.">
                  <ProjectsForm entries={data.projects} onChange={projects => setData(d => ({ ...d, projects }))} />
                </SectionWrapper>
              </TabsContent>

              <TabsContent value="skills">
                <SectionWrapper title="Technical Skills" description="Group your skills by category (e.g. Languages, Frameworks, Tools).">
                  <SkillsForm entries={data.skills} onChange={skills => setData(d => ({ ...d, skills }))} />
                </SectionWrapper>
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Preview panel */}
        {showPreview && (
          <div className="hidden lg:flex flex-col bg-zinc-300 dark:bg-zinc-700 overflow-auto">
            <div className="sticky top-0 z-10 bg-muted/80 backdrop-blur border-b px-4 py-2 flex items-center justify-end shrink-0">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Live Preview</span>
            </div>
            <div ref={previewPanelRef} className="p-4 overflow-x-hidden flex justify-center">
              {/* Outer div collapses to the post-scale visual size so no excess whitespace */}
              <div style={{
                width: `${Math.round(IFRAME_WIDTH_PX * previewScale)}px`,
                height: `${Math.round(IFRAME_HEIGHT_PX * previewScale)}px`,
                overflow: 'hidden',
              }}>
                <div style={{
                  transform: `scale(${previewScale})`,
                  transformOrigin: 'top left',
                  width: `${IFRAME_WIDTH_PX}px`,
                  height: `${IFRAME_HEIGHT_PX}px`,
                }}>
                  <ResumePreview data={toAPIData(data)} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
