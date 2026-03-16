import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, X } from 'lucide-react';

function newCategory(name = '') {
  return { id: crypto.randomUUID(), category: name, skills: [] };
}

const SUGGESTED = ['Languages', 'Frameworks', 'Tools', 'Databases', 'Cloud', 'Libraries'];

function SkillTagInput({ skills, onChange }) {
  const [draft, setDraft] = useState('');

  const add = () => {
    const val = draft.trim();
    if (!val || skills.includes(val)) return;
    onChange([...skills, val]);
    setDraft('');
  };

  const remove = (skill) => onChange(skills.filter(s => s !== skill));

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); add(); }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input placeholder="Add skill and press Enter..." value={draft} onChange={e => setDraft(e.target.value)} onKeyDown={handleKeyDown} />
        <Button type="button" variant="outline" size="sm" onClick={add} className="shrink-0">
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      {skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {skills.map(skill => (
            <Badge key={skill} variant="secondary" className="gap-1 pr-1">
              {skill}
              <button onClick={() => remove(skill)} className="hover:text-destructive ml-0.5">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SkillsForm({ entries, onChange }) {
  const update = (id, field, value) =>
    onChange(entries.map(e => e.id === id ? { ...e, [field]: value } : e));
  const remove = (id) => onChange(entries.filter(e => e.id !== id));
  const add = (name = '') => onChange([...entries, newCategory(name)]);

  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs text-muted-foreground mb-2">Quick add:</p>
        <div className="flex flex-wrap gap-1">
          {SUGGESTED.filter(c => !entries.some(e => e.category === c)).map(cat => (
            <button
              key={cat}
              onClick={() => add(cat)}
              className="text-xs px-2 py-1 rounded border border-dashed text-muted-foreground hover:text-foreground hover:border-foreground transition-colors"
            >
              + {cat}
            </button>
          ))}
        </div>
      </div>

      {entries.map((entry) => (
        <div key={entry.id} className="space-y-3 p-4 border rounded-lg bg-muted/20">
          <div className="flex items-center gap-3">
            <div className="flex-1 space-y-1.5">
              <Label>Category Name</Label>
              <Input
                placeholder="e.g. Languages"
                value={entry.category}
                onChange={e => update(entry.id, 'category', e.target.value)}
              />
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive mt-6 shrink-0" onClick={() => remove(entry.id)}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
          <SkillTagInput skills={entry.skills} onChange={skills => update(entry.id, 'skills', skills)} />
        </div>
      ))}

      <Button variant="outline" size="sm" className="w-full gap-2" onClick={() => add()}>
        <Plus className="h-4 w-4" />
        Add Skill Category
      </Button>
    </div>
  );
}
