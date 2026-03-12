import React, { useRef, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, X, ChevronDown, ChevronUp, Search, FolderOpen } from 'lucide-react';

// Placeholder project list — will be replaced with API data
const MOCK_PROJECTS = [];

function MyProjectsList() {
  const [search, setSearch] = useState('');

  const filtered = MOCK_PROJECTS.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

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
            {MOCK_PROJECTS.length === 0
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
                  {[proj.languages?.slice(0, 3).join(', '), proj.date_label]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </div>
              <Button type="button" size="sm" variant="outline" className="shrink-0 h-7 text-xs">
                Add
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function AutofillPanel() {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('projects'); // 'projects' | 'zip' | 'github'
  const [githubUrl, setGithubUrl] = useState('');
  const fileRef = useRef(null);

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

          {mode === 'projects' && <MyProjectsList />}

          {mode === 'zip' && (
            <div className="space-y-1.5">
              <Label>Upload ZIP file</Label>
              <input
                ref={fileRef}
                type="file"
                accept=".zip"
                className="block w-full text-sm text-muted-foreground file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
              />
              <p className="text-xs text-muted-foreground">Analyzes the ZIP and autofills a new project entry.</p>
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
                />
                <Button type="button" size="sm" disabled={!githubUrl.trim()} className="shrink-0">
                  Analyze
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

export default function ProjectsForm({ entries, onChange }) {
  const update = (id, field, value) =>
    onChange(entries.map(e => e.id === id ? { ...e, [field]: value } : e));
  const remove = (id) => onChange(entries.filter(e => e.id !== id));
  const add = () => onChange([...entries, newEntry()]);

  return (
    <div className="space-y-4">
      <AutofillPanel />
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
