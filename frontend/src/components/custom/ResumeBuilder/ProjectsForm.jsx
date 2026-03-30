import React, { useEffect, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, X, ChevronDown, ChevronUp, Search, FolderOpen } from 'lucide-react';
import {
  listProjects,
  getProjectResumeLatest,
  getProjectSkillSources,
  analyzeZipUpload,
  analyzeGitHubUrl,
} from '@/lib/resumeBuilderApi';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDateLabel(isoStr) {
  if (!isoStr) return '';
  try {
    return new Date(isoStr).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  } catch {
    return '';
  }
}

/**
 * Build { Languages, Frameworks, Libraries, Tools } dict from a SkillSourceResponse.breakdown.
 * Only includes non-empty categories.
 */
function buildSkillsDict(breakdown) {
  const map = {
    Languages: breakdown.from_languages,
    Frameworks: breakdown.from_frameworks,
    Libraries: breakdown.from_libraries,
    Tools: breakdown.from_tools,
  };
  const result = {};
  for (const [cat, skills] of Object.entries(map)) {
    if (skills?.length) result[cat] = skills.map(s => s.name);
  }
  return result;
}

/**
 * Build a flat, deduplicated technologies array from a SkillSourceResponse.breakdown.
 * Max 15 entries.
 */
function buildTechFromSources(skillSources) {
  if (!skillSources?.breakdown) return [];
  const { from_languages, from_frameworks, from_libraries, from_tools } = skillSources.breakdown;
  const all = [
    ...(from_languages || []),
    ...(from_frameworks || []),
    ...(from_libraries || []).slice(0, 5),
    ...(from_tools || []).slice(0, 5),
  ].map(s => s.name);
  return [...new Set(all)].slice(0, 15);
}

/**
 * Fetch resume highlights + skill sources for a project in parallel,
 * then build and return a project form entry plus a skills dict.
 */
async function fetchProjectData(projectId, name, techOverride, dateLabel) {
  const [resumeItem, skillSources] = await Promise.all([
    getProjectResumeLatest(projectId).catch(() => null),
    getProjectSkillSources(projectId).catch(() => null),
  ]);

  const technologies = techOverride.length ? techOverride : buildTechFromSources(skillSources);
  const skillsDict = skillSources?.breakdown ? buildSkillsDict(skillSources.breakdown) : {};

  return {
    entry: {
      id: crypto.randomUUID(),
      title: name,
      technologies: [...new Set(technologies)].slice(0, 15),
      date_label: dateLabel,
      highlights: resumeItem?.highlights || [],
    },
    skillsDict,
  };
}

// ---------------------------------------------------------------------------
// MyProjectsList — "My Projects" tab
// ---------------------------------------------------------------------------

function MyProjectsList({ entries, onChangeEntries, onAddSkills }) {
  const [search, setSearch] = useState('');
  const [projects, setProjects] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState(null);
  const [adding, setAdding] = useState(null); // project.id currently being added

  useEffect(() => {
    listProjects()
      .then(data => setProjects(data.items || []))
      .catch(err => setListError(err.response?.data?.detail || err.message || 'Failed to load projects'))
      .finally(() => setLoadingList(false));
  }, []);

  async function handleAdd(project) {
    setAdding(project.id);
    try {
      const date = project.first_commit_date || project.project_started_at || project.created_at;
      const { entry, skillsDict } = await fetchProjectData(
        project.id,
        project.name,
        [], // no tech override — will be built from skill sources
        formatDateLabel(date),
      );

      // Replace empty placeholder entries when adding the first project
      const nonEmpty = entries.filter(e => e.title);
      onChangeEntries([...nonEmpty, entry]);

      if (onAddSkills && Object.keys(skillsDict).length) {
        onAddSkills(skillsDict);
      }
    } catch (err) {
      alert(`Failed to add project: ${err.message}`);
    } finally {
      setAdding(null);
    }
  }

  const filtered = projects.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  if (loadingList) {
    return <div className="py-6 text-center text-sm text-muted-foreground">Loading projects…</div>;
  }

  if (listError) {
    return <div className="py-6 text-center text-sm text-destructive">{listError}</div>;
  }

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
        <Input
          placeholder="Search projects…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="pl-8 h-8 text-sm"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-6 text-center text-muted-foreground">
          <FolderOpen className="h-8 w-8 opacity-40" />
          <p className="text-sm">
            {projects.length === 0
              ? 'No analyzed projects found. Upload a ZIP or add a GitHub URL first.'
              : 'No projects match your search.'}
          </p>
        </div>
      ) : (
        <ul className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
          {filtered.map(proj => (
            <li
              key={proj.id}
              className="flex items-center justify-between gap-3 rounded-md border bg-background px-3 py-2 text-sm"
            >
              <div className="min-w-0">
                <p className="font-medium truncate">{proj.name}</p>
                <p className="text-xs text-muted-foreground truncate">
                  {[
                    proj.language_count ? `${proj.language_count} lang${proj.language_count !== 1 ? 's' : ''}` : null,
                    proj.skill_count ? `${proj.skill_count} skill${proj.skill_count !== 1 ? 's' : ''}` : null,
                  ].filter(Boolean).join(' · ')}
                </p>
              </div>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="shrink-0 h-7 text-xs"
                onClick={() => handleAdd(proj)}
                disabled={adding === proj.id}
              >
                {adding === proj.id ? '…' : 'Add'}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AutofillPanel — collapsed panel with three source modes
// ---------------------------------------------------------------------------

function AutofillPanel({ entries, onChangeEntries, onAddSkills }) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('projects'); // 'projects' | 'zip' | 'github'
  const [githubUrl, setGithubUrl] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const fileRef = useRef(null);

  /** Add a project from an AnalysisResult returned by the analyze endpoints. */
  async function addFromAnalysisResult(result) {
    const techOverride = [
      ...(result.languages || []),
      ...(result.frameworks || []),
      ...(result.tools_and_technologies || []),
    ];
    const date = result.first_commit_date || result.project_started_at;
    const { entry, skillsDict } = await fetchProjectData(
      result.project_id,
      result.project_name,
      techOverride,
      formatDateLabel(date),
    );

    const nonEmpty = entries.filter(e => e.title);
    onChangeEntries([...nonEmpty, entry]);

    if (onAddSkills && Object.keys(skillsDict).length) {
      onAddSkills(skillsDict);
    }
  }

  async function handleZipUpload() {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setAnalyzing(true);
    try {
      const results = await analyzeZipUpload(file, file.name.replace(/\.zip$/i, ''));
      if (results?.length > 0) {
        await addFromAnalysisResult(results[0]);
      }
    } catch (err) {
      alert(`Analysis failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setAnalyzing(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  async function handleGitHubAnalyze() {
    if (!githubUrl.trim()) return;
    setAnalyzing(true);
    try {
      const results = await analyzeGitHubUrl(githubUrl.trim());
      if (results?.length > 0) {
        await addFromAnalysisResult(results[0]);
        setGithubUrl('');
      }
    } catch (err) {
      alert(`Analysis failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="border rounded-lg bg-muted/10">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium hover:bg-muted/30 rounded-lg transition-colors"
      >
        <span>Autofill from project analysis</span>
        {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t pt-3">
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant={mode === 'projects' ? 'default' : 'outline'}
              onClick={() => setMode('projects')}
            >
              My Projects
            </Button>
            <Button
              type="button"
              size="sm"
              variant={mode === 'zip' ? 'default' : 'outline'}
              onClick={() => setMode('zip')}
            >
              ZIP Upload
            </Button>
            <Button
              type="button"
              size="sm"
              variant={mode === 'github' ? 'default' : 'outline'}
              onClick={() => setMode('github')}
            >
              GitHub URL
            </Button>
          </div>

          {mode === 'projects' && (
            <MyProjectsList
              entries={entries}
              onChangeEntries={onChangeEntries}
              onAddSkills={onAddSkills}
            />
          )}

          {mode === 'zip' && (
            <div className="space-y-2">
              <Label>Upload ZIP file</Label>
              <input
                ref={fileRef}
                type="file"
                accept=".zip"
                className="block w-full text-sm text-muted-foreground file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
              />
              <Button
                type="button"
                size="sm"
                onClick={handleZipUpload}
                disabled={analyzing}
                className="w-full"
              >
                {analyzing ? 'Analyzing…' : 'Analyze & Add'}
              </Button>
              <p className="text-xs text-muted-foreground">
                Analyzes the ZIP and autofills a new project entry.
              </p>
            </div>
          )}

          {mode === 'github' && (
            <div className="space-y-1.5">
              <Label>GitHub repository URL</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="https://github.com/user/repo"
                  value={githubUrl}
                  onChange={e => setGithubUrl(e.target.value)}
                  disabled={analyzing}
                />
                <Button
                  type="button"
                  size="sm"
                  onClick={handleGitHubAnalyze}
                  disabled={!githubUrl.trim() || analyzing}
                  className="shrink-0"
                >
                  {analyzing ? 'Analyzing…' : 'Analyze'}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">Public repositories only.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// TagInput & BulletEditor (unchanged sub-components)
// ---------------------------------------------------------------------------

function newEntry() {
  return {
    id: crypto.randomUUID(),
    title: '',
    technologies: [],
    date_label: '',
    highlights: [],
  };
}

function TagInput({ tags, onChange, placeholder }) {
  const [draft, setDraft] = useState('');

  const add = () => {
    const val = draft.trim();
    if (!val || tags.includes(val)) return;
    onChange([...tags, val]);
    setDraft('');
  };

  const remove = (tag) => onChange(tags.filter(t => t !== tag));

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); add(); }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input placeholder={placeholder} value={draft} onChange={e => setDraft(e.target.value)} onKeyDown={handleKeyDown} />
        <Button type="button" variant="outline" size="sm" onClick={add} className="shrink-0">
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {tags.map(tag => (
            <Badge key={tag} variant="secondary" className="gap-1 pr-1">
              {tag}
              <button onClick={() => remove(tag)} className="hover:text-destructive ml-0.5">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function BulletEditor({ bullets, onChange, label, placeholder }) {
  const [draft, setDraft] = useState('');

  const add = () => {
    if (!draft.trim()) return;
    onChange([...bullets, draft.trim()]);
    setDraft('');
  };

  const remove = (idx) => onChange(bullets.filter((_, i) => i !== idx));

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); add(); }
  };

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex gap-2">
        <Input placeholder={placeholder} value={draft} onChange={e => setDraft(e.target.value)} onKeyDown={handleKeyDown} />
        <Button type="button" variant="outline" size="sm" onClick={add} className="shrink-0">
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <ul className="space-y-1">
        {bullets.map((b, i) => (
          <li key={i} className="flex items-start gap-2 text-sm bg-muted/30 rounded px-2 py-1.5">
            <span className="mt-0.5 shrink-0 text-muted-foreground">•</span>
            <span className="flex-1">{b}</span>
            <button onClick={() => remove(i)} className="shrink-0 text-muted-foreground hover:text-destructive">
              <X className="h-3.5 w-3.5" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ProjectsForm — main export
// ---------------------------------------------------------------------------

export default function ProjectsForm({ entries, onChange, onAddSkills }) {
  const update = (id, field, value) =>
    onChange(entries.map(e => e.id === id ? { ...e, [field]: value } : e));
  const remove = (id) => onChange(entries.filter(e => e.id !== id));
  const add = () => onChange([...entries, newEntry()]);

  return (
    <div className="space-y-4">
      <AutofillPanel
        entries={entries}
        onChangeEntries={onChange}
        onAddSkills={onAddSkills}
      />
      {entries.map((proj, idx) => (
        <div key={proj.id} className="space-y-3 p-4 border rounded-lg bg-muted/20">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Project {idx + 1}</span>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => remove(proj.id)}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Project Title *</Label>
              <Input placeholder="My Awesome App" value={proj.title} onChange={e => update(proj.id, 'title', e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Date Label</Label>
              <Input placeholder="Jan 2025 – Present" value={proj.date_label} onChange={e => update(proj.id, 'date_label', e.target.value)} />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Technologies</Label>
            <TagInput
              tags={proj.technologies}
              onChange={tags => update(proj.id, 'technologies', tags)}
              placeholder="Add technology and press Enter (e.g. React)"
            />
          </div>

          <BulletEditor
            label="Highlights"
            placeholder="Add a highlight and press Enter..."
            bullets={proj.highlights}
            onChange={highlights => update(proj.id, 'highlights', highlights)}
          />
        </div>
      ))}

      <Button variant="outline" size="sm" className="w-full gap-2" onClick={add}>
        <Plus className="h-4 w-4" />
        Add Project
      </Button>
    </div>
  );
}
