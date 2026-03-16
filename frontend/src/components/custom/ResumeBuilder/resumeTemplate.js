/**
 * Single source of truth for the Jake's Resume HTML template.
 * CSS is taken verbatim from backend/src/templates/resume_jake.html.
 */

const JAKE_CSS = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html { background: #fff; }
  body {
    font-family: 'Times New Roman', Times, serif;
    font-size: 11pt;
    color: #000;
    background: #fff;
    padding: 0.5in;
    line-height: 1.2;
  }
  .header { text-align: center; margin-bottom: 4px; }
  .header h1 {
    font-size: 22pt;
    font-weight: bold;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }
  .contact-row { font-size: 10pt; text-align: center; }
  .contact-row a { color: #000; text-decoration: none; }
  .contact-row .sep { margin: 0 4px; }
  .section { margin-top: 8px; }
  .section-title {
    font-size: 12pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #000;
    padding-bottom: 1px;
    margin-bottom: 4px;
  }
  .entry-header { display: flex; justify-content: space-between; align-items: baseline; }
  .entry-org { font-weight: bold; }
  .entry-date { font-style: italic; white-space: nowrap; }
  .entry-sub { display: flex; justify-content: space-between; align-items: baseline; }
  .entry-title { font-style: italic; }
  .entry-location { font-style: italic; white-space: nowrap; }
  ul.bullets { margin-left: 16px; margin-top: 2px; }
  ul.bullets li { margin-bottom: 1px; list-style-type: disc; }
  .project-header { display: flex; justify-content: space-between; align-items: baseline; }
  .project-title { font-weight: bold; }
  .project-tech { font-style: italic; }
  .skills-row { margin-bottom: 2px; }
  .skills-row strong { font-weight: bold; }
  .entry { margin-bottom: 4px; }
`;

function formatDate(dateStr) {
  if (!dateStr) return '';
  const [year, month] = dateStr.split('-');
  const d = new Date(Number(year), Number(month) - 1);
  return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Builds the full Jake resume HTML string from resume data.
 * @param {{ contact, summary, education, experience, projects, skills }} data
 * @returns {string} complete HTML document
 */
export function buildResumeHTML({ contact, summary, education, experience, projects, skills }) {
  // ── Header ──
  const contactParts = [];
  if (contact.phone) contactParts.push(esc(contact.phone));
  if (contact.email) contactParts.push(`<a href="mailto:${esc(contact.email)}">${esc(contact.email)}</a>`);
  if (contact.linkedin_url) contactParts.push(`<a href="${esc(contact.linkedin_url)}">${esc(contact.linkedin_url)}</a>`);
  if (contact.github_url) contactParts.push(`<a href="${esc(contact.github_url)}">${esc(contact.github_url)}</a>`);
  if (contact.portfolio_url) contactParts.push(`<a href="${esc(contact.portfolio_url)}">${esc(contact.portfolio_url)}</a>`);
  if (contact.location) contactParts.push(esc(contact.location));
  const contactHTML = contactParts.join(' <span class="sep">|</span> ');

  // ── Summary ──
  const summaryHTML = summary
    ? `<div class="section"><div class="section-title">Summary</div><p>${esc(summary)}</p></div>`
    : '';

  // ── Education ──
  const educationHTML = education.filter(e => e.institution).length
    ? `<div class="section">
        <div class="section-title">Education</div>
        ${education.filter(e => e.institution).map(edu => `
        <div class="entry">
          <div class="entry-header">
            <span class="entry-org">${esc(edu.institution)}</span>
            <span class="entry-date">${formatDate(edu.start_date)} &ndash; ${edu.is_current ? 'Present' : (edu.end_date ? formatDate(edu.end_date) : '')}</span>
          </div>
          <div class="entry-sub">
            <span class="entry-title">${esc(edu.degree)}${edu.field_of_study ? ` in ${esc(edu.field_of_study)}` : ''}</span>
            ${edu.location ? `<span class="entry-location">${esc(edu.location)}</span>` : ''}
          </div>
          ${edu.gpa ? `<div style="font-style:italic">GPA: ${esc(edu.gpa)}</div>` : ''}
        </div>`).join('')}
      </div>`
    : '';

  // ── Experience ──
  // Mirrors resume_jake.html: combines responsibilities + achievements into one bullet list
  const experienceHTML = experience.filter(e => e.company_name).length
    ? `<div class="section">
        <div class="section-title">Experience</div>
        ${experience.filter(e => e.company_name).map(exp => {
          const allBullets = [
            ...(exp.responsibilities || []),
            ...(exp.achievements || []),
          ].filter(b => b.trim());
          return `
          <div class="entry">
            <div class="entry-header">
              <span class="entry-org">${esc(exp.company_name)}</span>
              <span class="entry-date">${formatDate(exp.start_date)} &ndash; ${exp.is_current ? 'Present' : (exp.end_date ? formatDate(exp.end_date) : '')}</span>
            </div>
            <div class="entry-sub">
              <span class="entry-title">${esc(exp.job_title)}${exp.is_remote ? ' (Remote)' : ''}</span>
              ${exp.location ? `<span class="entry-location">${esc(exp.location)}</span>` : ''}
            </div>
            ${allBullets.length ? `<ul class="bullets">${allBullets.map(b => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
          </div>`;
        }).join('')}
      </div>`
    : '';

  // ── Projects ──
  const projectsHTML = projects.filter(p => p.title).length
    ? `<div class="section">
        <div class="section-title">Projects</div>
        ${projects.filter(p => p.title).map(proj => {
          const highlights = proj.highlights.filter(h => h.trim());
          return `
          <div class="entry">
            <div class="project-header">
              <span>
                <span class="project-title">${esc(proj.title)}</span>
                ${proj.technologies.length ? `<span class="project-tech"> | ${proj.technologies.map(esc).join(', ')}</span>` : ''}
              </span>
              ${proj.date_label ? `<span class="entry-date">${esc(proj.date_label)}</span>` : ''}
            </div>
            ${highlights.length ? `<ul class="bullets">${highlights.map(h => `<li>${esc(h)}</li>`).join('')}</ul>` : ''}
          </div>`;
        }).join('')}
      </div>`
    : '';

  // ── Technical Skills ──
  // skills is Dict<string, string[]> matching FullResumeData schema
  const skillEntries = Object.entries(skills).filter(([cat, list]) => cat && list.length);
  const skillsHTML = skillEntries.length
    ? `<div class="section">
        <div class="section-title">Technical Skills</div>
        ${skillEntries.map(([cat, list]) =>
          `<div class="skills-row"><strong>${esc(cat)}:</strong> ${list.map(esc).join(', ')}</div>`
        ).join('')}
      </div>`
    : '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(contact.name)} - Resume</title>
  <style>${JAKE_CSS}</style>
</head>
<body>
  <div class="header">
    <h1>${esc(contact.name) || 'Your Name'}</h1>
    <div class="contact-row">${contactHTML}</div>
  </div>
  ${summaryHTML}
  ${educationHTML}
  ${experienceHTML}
  ${projectsHTML}
  ${skillsHTML}
</body>
</html>`;
}
