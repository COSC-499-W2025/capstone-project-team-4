import React, { useMemo } from 'react';
import { buildResumeHTML } from './resumeTemplate';

const PLACEHOLDER_DATA = {
  contact: {
    name: 'Jane Doe',
    phone: '(604) 555-0123',
    email: 'jane.doe@email.com',
    linkedin_url: 'linkedin.com/in/janedoe',
    github_url: 'github.com/janedoe',
    portfolio_url: '',
    location: 'Vancouver, BC',
  },
  summary:
    'Computer Science student with hands-on experience building full-stack web applications and REST APIs. Passionate about clean architecture, developer tooling, and open source.',
  education: [
    {
      institution: 'University of British Columbia',
      degree: 'Bachelor of Science',
      field_of_study: 'Computer Science',
      start_date: '2021-09',
      end_date: '2025-04',
      is_current: false,
      location: 'Kelowna, BC',
      gpa: '3.8',
    },
  ],
  experience: [
    {
      company_name: 'Acme Corp',
      job_title: 'Software Developer Intern',
      start_date: '2024-05',
      end_date: '2024-08',
      is_current: false,
      location: 'Vancouver, BC',
      is_remote: false,
      responsibilities: [
        'Built and maintained RESTful APIs serving 50k+ daily active users using FastAPI and PostgreSQL.',
        'Reduced average API response time by 30% through query optimisation and Redis caching.',
      ],
      achievements: [
        'Delivered a self-service analytics dashboard two weeks ahead of schedule, adopted by 3 internal teams.',
      ],
    },
  ],
  projects: [
    {
      title: 'Project Analyzer',
      technologies: ['Python', 'FastAPI', 'React', 'SQLite'],
      date_label: 'Jan 2025 – Apr 2025',
      highlights: [
        'Developed a tool that parses GitHub repositories and generates resume bullet points from code analysis.',
        'Implemented AST-based cyclomatic complexity metrics across Python, JavaScript, and TypeScript.',
        'Containerised the full stack with Docker Compose for one-command local setup.',
      ],
    },
    {
      title: 'Personal Portfolio',
      technologies: ['Next.js', 'Tailwind CSS', 'Vercel'],
      date_label: 'Sep 2023',
      highlights: [
        'Designed and deployed a responsive portfolio site with a 95+ Lighthouse performance score.',
      ],
    },
  ],
  skills: {
    Languages: ['Python', 'JavaScript', 'TypeScript', 'SQL'],
    Frameworks: ['FastAPI', 'React', 'Next.js', 'SQLAlchemy'],
    Tools: ['Git', 'Docker', 'GitHub Actions', 'Redis'],
  },
};

function isDataEmpty(data) {
  return (
    !data.contact.name &&
    !data.summary &&
    !data.education.some(e => e.institution) &&
    !data.experience.some(e => e.company_name) &&
    !data.projects.some(p => p.title) &&
    !Object.keys(data.skills).length
  );
}

export default function ResumePreview({ data }) {
  const isEmpty = isDataEmpty(data);
  const html = useMemo(
    () => buildResumeHTML(isEmpty ? PLACEHOLDER_DATA : data),
     
    [data, isEmpty],
  );

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      {isEmpty && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 10,
            background: 'rgba(59,130,246,0.08)',
            borderBottom: '1px solid rgba(59,130,246,0.25)',
            padding: '6px 12px',
            textAlign: 'center',
            fontSize: '11px',
            color: '#2563eb',
            fontFamily: 'sans-serif',
            letterSpacing: '0.02em',
          }}
        >
          Sample preview — fill in the form on the left to see your own resume here
        </div>
      )}
      <iframe
        srcDoc={html}
        title="Resume Preview"
        style={{
          width: '8.5in',
          height: '11in',
          border: 'none',
          display: 'block',
          background: '#fff',
          boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
        }}
      />
    </div>
  );
}
