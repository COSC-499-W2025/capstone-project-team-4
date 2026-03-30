import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Trash2, X } from 'lucide-react';

function newEntry() {
  return {
    id: crypto.randomUUID(),
    company_name: '',
    job_title: '',
    location: '',
    is_remote: false,
    start_date: '',
    end_date: '',
    is_current: false,
    responsibilities: [],
    achievements: [],
  };
}

function BulletEditor({ label, items, onChange, placeholder }) {
  const [draft, setDraft] = useState('');

  const add = () => {
    if (!draft.trim()) return;
    onChange([...items, draft.trim()]);
    setDraft('');
  };

  const remove = (idx) => onChange(items.filter((_, i) => i !== idx));

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); add(); }
  };

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex gap-2">
        <Input
          placeholder={placeholder}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <Button type="button" variant="outline" size="sm" onClick={add} className="shrink-0">
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <ul className="space-y-1">
        {items.map((b, i) => (
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

export default function ExperienceForm({ entries, onChange }) {
  const update = (id, field, value) =>
    onChange(entries.map(e => e.id === id ? { ...e, [field]: value } : e));
  const remove = (id) => onChange(entries.filter(e => e.id !== id));
  const add = () => onChange([...entries, newEntry()]);

  return (
    <div className="space-y-4">
      {entries.map((exp, idx) => (
        <div key={exp.id} className="space-y-3 p-4 border rounded-lg bg-muted/20">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Entry {idx + 1}</span>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => remove(exp.id)}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Company *</Label>
              <Input placeholder="Acme Corp" value={exp.company_name} onChange={e => update(exp.id, 'company_name', e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Job Title *</Label>
              <Input placeholder="Software Engineer" value={exp.job_title} onChange={e => update(exp.id, 'job_title', e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Start Date</Label>
              <Input type="month" value={exp.start_date} onChange={e => update(exp.id, 'start_date', e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>End Date</Label>
              <Input type="month" value={exp.end_date} onChange={e => update(exp.id, 'end_date', e.target.value)} disabled={exp.is_current} />
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Checkbox
                id={`exp-current-${exp.id}`}
                checked={exp.is_current}
                onCheckedChange={v => update(exp.id, 'is_current', v)}
              />
              <Label htmlFor={`exp-current-${exp.id}`} className="text-sm font-normal cursor-pointer">Current position</Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id={`exp-remote-${exp.id}`}
                checked={exp.is_remote}
                onCheckedChange={v => update(exp.id, 'is_remote', v)}
              />
              <Label htmlFor={`exp-remote-${exp.id}`} className="text-sm font-normal cursor-pointer">Remote</Label>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Location</Label>
            <Input placeholder="Vancouver, BC" value={exp.location} onChange={e => update(exp.id, 'location', e.target.value)} />
          </div>

          <BulletEditor
            label="Responsibilities"
            placeholder="Add a responsibility and press Enter..."
            items={exp.responsibilities}
            onChange={v => update(exp.id, 'responsibilities', v)}
          />

          <BulletEditor
            label="Achievements"
            placeholder="Add an achievement and press Enter..."
            items={exp.achievements}
            onChange={v => update(exp.id, 'achievements', v)}
          />
        </div>
      ))}

      <Button variant="outline" size="sm" className="w-full gap-2" onClick={add}>
        <Plus className="h-4 w-4" />
        Add Experience
      </Button>
    </div>
  );
}
