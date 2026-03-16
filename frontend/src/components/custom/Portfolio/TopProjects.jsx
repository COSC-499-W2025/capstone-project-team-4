import { ExternalLink } from "lucide-react";

const ACCENT_COLORS = [
  { border: "#0d9488", leftBar: "#0d9488", badge: "#f0fdfa", badgeText: "#0d9488", badgeBorder: "#99f6e4" },
  { border: "#6366f1", leftBar: "#6366f1", badge: "#eef2ff", badgeText: "#6366f1", badgeBorder: "#c7d2fe" },
  { border: "#f59e0b", leftBar: "#f59e0b", badge: "#fffbeb", badgeText: "#d97706", badgeBorder: "#fde68a" },
];

export default function TopProjects({ portfolio }) {
  const projects = portfolio?.content?.projects ?? [];
  const top3 = [...projects]
    .sort((a, b) => (b.total_lines_of_code ?? 0) - (a.total_lines_of_code ?? 0))
    .slice(0, 3);

  return (
    <section>
      <h2 className="pf-section-title">Projects</h2>
      <div className="pf-divider" />

      {top3.length === 0 ? (
        <div className="pf-card" style={{ padding: 32, textAlign: "center", marginTop: 32 }}>
          <p style={{ color: "#94a3b8", fontSize: 14 }}>No projects found. Upload a project to get started.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 20, marginTop: 36 }}>
          {top3.map((project, index) => {
            const colors = ACCENT_COLORS[index];
            return (
              <div
                key={project.name ?? index}
                style={{
                  background: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: 14,
                  borderLeft: `4px solid ${colors.leftBar}`,
                  padding: 24,
                  boxShadow: "0 2px 8px rgba(15,23,42,0.06)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 14,
                  transition: "box-shadow 0.2s, transform 0.2s",
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = "translateY(-3px)";
                  e.currentTarget.style.boxShadow = "0 8px 24px rgba(15,23,42,0.1)";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 2px 8px rgba(15,23,42,0.06)";
                }}
              >
                {/* Rank + link */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{
                    background: colors.badge,
                    color: colors.badgeText,
                    border: `1px solid ${colors.badgeBorder}`,
                    borderRadius: 6,
                    padding: "2px 10px",
                    fontSize: 11,
                    fontWeight: 700,
                  }}>
                    #{index + 1}
                  </span>
                  {project.live_demo_url && (
                    <a href={project.live_demo_url} target="_blank" rel="noopener noreferrer" style={{ color: "#94a3b8" }}>
                      <ExternalLink style={{ width: 14, height: 14 }} />
                    </a>
                  )}
                </div>

                {/* Name */}
                <h3 style={{ fontSize: 17, fontWeight: 700, color: "#0f172a", fontFamily: "'Space Grotesk', sans-serif", margin: 0 }}>
                  {project.custom_name ?? project.name ?? "Unnamed Project"}
                </h3>

                {/* Description */}
                {project.description && (
                  <p style={{ fontSize: 13, color: "#64748b", lineHeight: 1.65, margin: 0, display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {project.description}
                  </p>
                )}

                {/* Language tags */}
                {project.languages?.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {project.languages.slice(0, 4).map((lang) => (
                      <span key={lang} className="pf-tag">{lang}</span>
                    ))}
                  </div>
                )}

                {/* Resume highlights */}
                {project.resume_highlights?.length > 0 && (
                  <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6 }}>
                    {project.resume_highlights.slice(0, 3).map((h, i) => (
                      <li key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                        <span style={{ color: colors.badgeText, marginTop: 3, flexShrink: 0, fontWeight: 700 }}>▸</span>
                        <span style={{ fontSize: 12, color: "#64748b", lineHeight: 1.5 }}>{h}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
