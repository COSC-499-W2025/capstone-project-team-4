import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';

export default function PersonalInfoForm({ contact, summary, onContactChange, onSummaryChange }) {
  const set = (field) => (e) => onContactChange({ ...contact, [field]: e.target.value });

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="pi-name">Full Name *</Label>
        <Input id="pi-name" placeholder="Jane Doe" value={contact.name} onChange={set('name')} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="pi-email">Email *</Label>
          <Input id="pi-email" type="email" placeholder="jane@example.com" value={contact.email} onChange={set('email')} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="pi-phone">Phone</Label>
          <Input id="pi-phone" placeholder="+1 (555) 000-0000" value={contact.phone} onChange={set('phone')} />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="pi-linkedin">LinkedIn URL</Label>
        <Input id="pi-linkedin" placeholder="linkedin.com/in/janedoe" value={contact.linkedin_url} onChange={set('linkedin_url')} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="pi-github">GitHub URL</Label>
        <Input id="pi-github" placeholder="github.com/janedoe" value={contact.github_url} onChange={set('github_url')} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="pi-portfolio">Portfolio URL</Label>
        <Input id="pi-portfolio" placeholder="janedoe.dev" value={contact.portfolio_url} onChange={set('portfolio_url')} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="pi-location">Location</Label>
        <Input id="pi-location" placeholder="Vancouver, BC" value={contact.location} onChange={set('location')} />
      </div>

      <Separator />

      <div className="space-y-1.5">
        <Label htmlFor="pi-summary">Professional Summary</Label>
        <Textarea
          id="pi-summary"
          placeholder="A brief paragraph about your background, key skills, and career goals..."
          value={summary}
          onChange={(e) => onSummaryChange(e.target.value)}
          rows={4}
          className="resize-none"
        />
        <p className="text-xs text-muted-foreground">Optional. Leave blank to omit this section.</p>
      </div>
    </div>
  );
}
