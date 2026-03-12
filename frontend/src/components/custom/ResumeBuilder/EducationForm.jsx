import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Trash2 } from 'lucide-react';

function newEntry() {
  return {
    id: crypto.randomUUID(),
    institution: '',
    degree: '',
    field_of_study: '',
    start_date: '',
    end_date: '',
    is_current: false,
    location: '',
    gpa: '',
  };
}

export default function EducationForm({ entries, onChange }) {
  const update = (id, field, value) =>
    onChange(entries.map(e => e.id === id ? { ...e, [field]: value } : e));
  const remove = (id) => onChange(entries.filter(e => e.id !== id));
  const add = () => onChange([...entries, newEntry()]);

  return (
    <div className="space-y-4">
      {entries.map((edu, idx) => (
        <div key={edu.id} className="space-y-3 p-4 border rounded-lg bg-muted/20">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Entry {idx + 1}</span>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => remove(edu.id)}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-1.5">
            <Label>Institution *</Label>
            <Input placeholder="University of British Columbia" value={edu.institution} onChange={e => update(edu.id, 'institution', e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Degree</Label>
              <Input placeholder="Bachelor of Science" value={edu.degree} onChange={e => update(edu.id, 'degree', e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Field of Study</Label>
              <Input placeholder="Computer Science" value={edu.field_of_study} onChange={e => update(edu.id, 'field_of_study', e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Start Date</Label>
              <Input type="month" value={edu.start_date} onChange={e => update(edu.id, 'start_date', e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>End Date</Label>
              <Input type="month" value={edu.end_date} onChange={e => update(edu.id, 'end_date', e.target.value)} disabled={edu.is_current} />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Checkbox
              id={`edu-current-${edu.id}`}
              checked={edu.is_current}
              onCheckedChange={v => update(edu.id, 'is_current', v)}
            />
            <Label htmlFor={`edu-current-${edu.id}`} className="text-sm font-normal cursor-pointer">Currently enrolled</Label>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Location</Label>
              <Input placeholder="Vancouver, BC" value={edu.location} onChange={e => update(edu.id, 'location', e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>GPA</Label>
              <Input placeholder="3.9" value={edu.gpa} onChange={e => update(edu.id, 'gpa', e.target.value)} />
            </div>
          </div>
        </div>
      ))}

      <Button variant="outline" size="sm" className="w-full gap-2" onClick={add}>
        <Plus className="h-4 w-4" />
        Add Education
      </Button>
    </div>
  );
}
