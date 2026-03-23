import { ExternalLink, Star, ListFilter } from "lucide-react";
import { useState, useMemo } from "react";
import axios from "axios";
import { getAccessToken } from "@/lib/auth";

const ACCENT_COLORS = [
  {
    border: "#0d9488",
    leftBar: "#0d9488",
    badge: "#f0fdfa",
    badgeText: "#0d9488",
    badgeBorder: "#99f6e4",
  },
  {
    border: "#6366f1",
    leftBar: "#6366f1",
    badge: "#eef2ff",
    badgeText: "#6366f1",
    badgeBorder: "#c7d2fe",
  },
  {
    border: "#f59e0b",
    leftBar: "#f59e0b",
    badge: "#fffbeb",
    badgeText: "#d97706",
    badgeBorder: "#fde68a",
  },
];

const SORT_OPTIONS = [
  { label: "Lines of Code", value: "total_lines_of_code" },
  { label: "Files Analyzed", value: "file_count" },
  { label: "Skills", value: "skill_count" },
  { label: "Contributors", value: "contributor_count" },
];

export default function TopProjects({
  portfolio,
  isPrivate,
  featuredIds,
  onFeaturedIdsChange,
  pinnedIds,
  onPinnedIdsChange,
  selectedProjectId,
  onSelectProject,
  onPortfolioUpdate,
}) {
  const [sortBy, setSortBy] = useState("total_lines_of_code");
  const [savingFeature, setSavingFeature] = useState(null);
  const [showPicker, setShowPicker] = useState(false);
  const [pickerSelection, setPickerSelection] = useState(new Set());

  const authHeader = useMemo(() => {
    const token = getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : null;
  }, []);

  const projects = portfolio?.content?.projects ?? [];

  const displayProjects = isPrivate
    ? pinnedIds?.size > 0
      ? projects.filter((p) => pinnedIds.has(p.id))
      : [...projects].sort((a, b) => (b[sortBy] ?? 0) - (a[sortBy] ?? 0))
    : projects.filter((p) => featuredIds?.has(p.id));

  const top3 = displayProjects.slice(0, 3);

  function handleOpenPicker() {
    setPickerSelection(new Set(featuredIds));
    setShowPicker(true);
  }

  function handlePickerToggle(id) {
    setPickerSelection((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < 3) {
        next.add(id);
      }
      return next;
    });
  }

  async function handlePickerConfirm() {
    const toAdd = [...pickerSelection].filter((id) => !featuredIds?.has(id));
    const toRemove = [...(featuredIds ?? [])].filter(
      (id) => !pickerSelection.has(id),
    );

    onFeaturedIdsChange?.(new Set(pickerSelection));
    onPinnedIdsChange?.(new Set(pickerSelection));
    setShowPicker(false);

    await Promise.all([
      ...toAdd.map((id) => {
        const project = projects.find((p) => p.id === id);
        if (!project) return Promise.resolve();
        return axios
          .put(
            `/api/portfolio/${portfolio.id}/projects/${encodeURIComponent(project.name)}/customize`,
            { is_featured: true },
            { headers: authHeader },
          )
          .catch((err) =>
            console.error(
              "Failed to feature",
              project.name,
              err?.response?.data || err,
            ),
          );
      }),
      ...toRemove.map((id) => {
        const project = projects.find((p) => p.id === id);
        if (!project) return Promise.resolve();
        return axios
          .put(
            `/api/portfolio/${portfolio.id}/projects/${encodeURIComponent(project.name)}/customize`,
            { is_featured: false },
            { headers: authHeader },
          )
          .catch((err) =>
            console.error(
              "Failed to unfeature",
              project.name,
              err?.response?.data || err,
            ),
          );
      }),
    ]);
  }

  async function handleToggleFeatured(project) {
    if (!portfolio?.id) return;
    setSavingFeature(project.id);

    onFeaturedIdsChange?.((prev) => {
      const next = new Set(prev);
      if (next.has(project.id)) next.delete(project.id);
      else next.add(project.id);
      return next;
    });

    try {
      const res = await axios.put(
        `/api/portfolio/${portfolio.id}/projects/${encodeURIComponent(project.name)}/customize`,
        { is_featured: !featuredIds?.has(project.id) },
        { headers: authHeader },
      );
      onPortfolioUpdate?.({
        ...res.data,
        content: {
          ...res.data.content,
          projects: [...res.data.content.projects],
        },
      });
    } catch (error) {
      onFeaturedIdsChange?.((prev) => {
        const next = new Set(prev);
        if (next.has(project.id)) next.delete(project.id);
        else next.add(project.id);
        return next;
      });
      console.error(
        "Failed to update featured status",
        error?.response?.data || error,
      );
    } finally {
      setSavingFeature(null);
    }
  }

  return (
    <section>
      <h2 className="pf-section-title">Projects</h2>
      <div className="pf-divider" />

      {isPrivate && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginTop: 20,
            flexWrap: "wrap",
          }}
        >
          <span style={{ fontSize: 12, color: "#64748b" }}>Sort by:</span>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {SORT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => {
                  setSortBy(opt.value);
                  onPinnedIdsChange?.(new Set());
                }}
                style={{
                  padding: "4px 12px",
                  borderRadius: 6,
                  border: `1px solid ${sortBy === opt.value && pinnedIds?.size === 0 ? "#0d9488" : "#e2e8f0"}`,
                  background:
                    sortBy === opt.value && pinnedIds?.size === 0
                      ? "#0d9488"
                      : "transparent",
                  color:
                    sortBy === opt.value && pinnedIds?.size === 0
                      ? "#ffffff"
                      : "#64748b",
                  fontSize: 12,
                  fontWeight: 500,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  transition: "all 0.15s",
                }}
              >
                {opt.label}
              </button>
            ))}
            <button
              onClick={handleOpenPicker}
              style={{
                padding: "4px 12px",
                borderRadius: 6,
                border: `1px solid ${pinnedIds?.size > 0 ? "#0d9488" : "#e2e8f0"}`,
                background: pinnedIds?.size > 0 ? "#0d9488" : "transparent",
                color: pinnedIds?.size > 0 ? "#ffffff" : "#64748b",
                fontSize: 12,
                fontWeight: 500,
                cursor: "pointer",
                fontFamily: "inherit",
                transition: "all 0.15s",
                display: "flex",
                alignItems: "center",
                gap: 5,
              }}
            >
              <ListFilter style={{ width: 12, height: 12 }} />
              Choose Projects
              {pinnedIds?.size > 0 && (
                <span
                  style={{
                    background: "#ffffff",
                    color: "#0d9488",
                    borderRadius: 10,
                    padding: "0 6px",
                    fontSize: 10,
                    fontWeight: 700,
                  }}
                >
                  {pinnedIds.size}
                </span>
              )}
            </button>
          </div>
          <span style={{ fontSize: 11, color: "#94a3b8", marginLeft: "auto" }}>
            ⭐ star a project to feature it in your public portfolio
          </span>
        </div>
      )}

      {!isPrivate && featuredIds?.size === 0 && (
        <p
          style={{
            fontSize: 12,
            color: "#94a3b8",
            textAlign: "center",
            marginTop: 16,
          }}
        >
          No featured projects — star projects in Private mode to feature them
          here.
        </p>
      )}

      {/* Choose Projects Modal */}
      {showPicker && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15,23,42,0.5)",
            zIndex: 50,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
          }}
        >
          <div
            style={{
              background: "#ffffff",
              borderRadius: 16,
              padding: 28,
              maxWidth: 480,
              width: "100%",
              boxShadow: "0 8px 32px rgba(15,23,42,0.16)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 8,
              }}
            >
              <h3
                style={{
                  fontSize: 16,
                  fontWeight: 700,
                  color: "#0f172a",
                  margin: 0,
                }}
              >
                Choose Featured Projects
              </h3>
              <span style={{ fontSize: 12, color: "#94a3b8" }}>
                {pickerSelection.size}/3 selected
              </span>
            </div>
            <p style={{ fontSize: 12, color: "#64748b", marginBottom: 16 }}>
              Select up to 3 projects to pin here and feature in your public
              portfolio.
            </p>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 8,
                maxHeight: 320,
                overflowY: "auto",
              }}
            >
              {projects.map((project) => {
                const selected = pickerSelection.has(project.id);
                const disabled = !selected && pickerSelection.size >= 3;
                return (
                  <div
                    key={project.id}
                    onClick={() => !disabled && handlePickerToggle(project.id)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      padding: "10px 14px",
                      borderRadius: 10,
                      border: `1px solid ${selected ? "#0d9488" : "#e2e8f0"}`,
                      background: selected ? "#f0fdfa" : "#ffffff",
                      cursor: disabled ? "not-allowed" : "pointer",
                      opacity: disabled ? 0.4 : 1,
                      transition: "all 0.15s",
                    }}
                  >
                    <div
                      style={{
                        width: 18,
                        height: 18,
                        borderRadius: 5,
                        border: `2px solid ${selected ? "#0d9488" : "#cbd5e1"}`,
                        background: selected ? "#0d9488" : "transparent",
                        flexShrink: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {selected && (
                        <span
                          style={{
                            color: "#fff",
                            fontSize: 11,
                            fontWeight: 700,
                          }}
                        >
                          ✓
                        </span>
                      )}
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <p
                        style={{
                          fontSize: 13,
                          fontWeight: 600,
                          color: "#0f172a",
                          margin: 0,
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {project.custom_name ?? project.name}
                      </p>
                      {project.languages?.length > 0 && (
                        <p
                          style={{
                            fontSize: 11,
                            color: "#94a3b8",
                            margin: "2px 0 0",
                          }}
                        >
                          {project.languages.slice(0, 3).join(", ")}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            <div
              style={{
                display: "flex",
                gap: 10,
                marginTop: 20,
                justifyContent: "flex-end",
              }}
            >
              <button
                onClick={() => setShowPicker(false)}
                style={{
                  padding: "7px 18px",
                  borderRadius: 8,
                  border: "1px solid #e2e8f0",
                  background: "transparent",
                  color: "#64748b",
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: "pointer",
                  fontFamily: "inherit",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handlePickerConfirm}
                style={{
                  padding: "7px 18px",
                  borderRadius: 8,
                  border: "none",
                  background: "#0d9488",
                  color: "#ffffff",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                  fontFamily: "inherit",
                }}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}

      {top3.length === 0 ? (
        <div
          className="pf-card"
          style={{ padding: 32, textAlign: "center", marginTop: 32 }}
        >
          <p style={{ color: "#94a3b8", fontSize: 14 }}>
            No projects found. Upload a project to get started.
          </p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 20,
            marginTop: 36,
          }}
        >
          {top3.map((project, index) => {
            const colors = ACCENT_COLORS[index];
            const isFeatured = featuredIds?.has(project.id) ?? false;
            return (
              // We can just use tailwind for this style but whatever lol
              <div
                key={project.id ?? index}
                style={{
                  background: "#ffffff",
                  border:
                    selectedProjectId === project.id
                      ? "2px solid #2563eb"
                      : "1px solid #e2e8f0",
                  borderRadius: 14,
                  borderLeft: `4px solid ${colors.leftBar}`,
                  padding: 24,
                  boxShadow: "0 2px 8px rgba(15,23,42,0.06)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: 14,
                  transition: "box-shadow 0.2s, transform 0.2s",
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-3px)";
                  e.currentTarget.style.boxShadow =
                    "0 8px 24px rgba(15,23,42,0.1)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow =
                    "0 2px 8px rgba(15,23,42,0.06)";
                }}
                onClick={() => {
                  onSelectProject?.(project.id);
                }}
              >
                {/* Rank + star + link */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <span
                    style={{
                      background: colors.badge,
                      color: colors.badgeText,
                      border: `1px solid ${colors.badgeBorder}`,
                      borderRadius: 6,
                      padding: "2px 10px",
                      fontSize: 11,
                      fontWeight: 700,
                    }}
                  >
                    #{index + 1}
                  </span>

                  <div
                    style={{ display: "flex", alignItems: "center", gap: 8 }}
                  >
                    {isPrivate && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleFeatured(project);
                        }}
                        disabled={savingFeature === project.id}
                        title={
                          isFeatured
                            ? "Remove from public portfolio"
                            : "Feature in public portfolio"
                        }
                        style={{
                          background: "none",
                          border: "none",
                          cursor:
                            savingFeature === project.id
                              ? "not-allowed"
                              : "pointer",
                          padding: 2,
                          opacity: savingFeature === project.id ? 0.5 : 1,
                        }}
                      >
                        <Star
                          style={{
                            width: 16,
                            height: 16,
                            fill: isFeatured ? "#f59e0b" : "none",
                            stroke: isFeatured ? "#f59e0b" : "#cbd5e1",
                          }}
                        />
                      </button>
                    )}
                    {project.live_demo_url && (
                      <a
                        href={project.live_demo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "#94a3b8" }}
                      >
                        <ExternalLink style={{ width: 14, height: 14 }} />
                      </a>
                    )}
                  </div>
                </div>

                {/* Name */}
                <h3
                  style={{
                    fontSize: 17,
                    fontWeight: 700,
                    color: "#0f172a",
                    fontFamily: "'Space Grotesk', sans-serif",
                    margin: 0,
                  }}
                >
                  {project.custom_name ?? project.name ?? "Unnamed Project"}
                </h3>

                {/* Description */}
                {project.description && (
                  <p
                    style={{
                      fontSize: 13,
                      color: "#64748b",
                      lineHeight: 1.65,
                      margin: 0,
                      display: "-webkit-box",
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                    }}
                  >
                    {project.description}
                  </p>
                )}

                {/* Language tags */}
                {project.languages?.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {project.languages.slice(0, 4).map((lang) => (
                      <span key={lang} className="pf-tag">
                        {lang}
                      </span>
                    ))}
                  </div>
                )}

                {/* Resume highlights */}
                {project.resume_highlights?.length > 0 && (
                  <ul
                    style={{
                      margin: 0,
                      padding: 0,
                      listStyle: "none",
                      display: "flex",
                      flexDirection: "column",
                      gap: 6,
                    }}
                  >
                    {project.resume_highlights.slice(0, 3).map((h, i) => (
                      <li
                        key={i}
                        style={{
                          display: "flex",
                          gap: 8,
                          alignItems: "flex-start",
                        }}
                      >
                        <span
                          style={{
                            color: colors.badgeText,
                            marginTop: 3,
                            flexShrink: 0,
                            fontWeight: 700,
                          }}
                        >
                          ▸
                        </span>
                        <span
                          style={{
                            fontSize: 12,
                            color: "#64748b",
                            lineHeight: 1.5,
                          }}
                        >
                          {h}
                        </span>
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
