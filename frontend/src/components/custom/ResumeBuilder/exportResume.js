import { getAccessToken } from '@/lib/auth';

/**
 * Export resume data via the backend API.
 * Uses POST /api/users/resume/export?format=<format> with FullResumeData as JSON body.
 * The backend renders with the Jake template (HTML/PDF via WeasyPrint/Markdown).
 *
 * @param {object} resumeData - FullResumeData-shaped object from toAPIData()
 * @param {'html'|'pdf'|'markdown'} format
 */
export async function exportResume(resumeData, format = 'html') {
  const token = getAccessToken();
  const res = await fetch(`/api/users/resume/export?format=${format}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(resumeData),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`Export failed (${res.status}): ${detail}`);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const disposition = res.headers.get('Content-Disposition') ?? '';
  const filename = disposition.match(/filename="(.+?)"/)?.[1]
    ?? `resume.${format === 'markdown' ? 'md' : format}`;

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
