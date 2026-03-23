import Navigation from "@/components/Navigation";
import { getAccessToken } from "@/lib/auth";
import axios from "axios";
import { AlertCircle, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import ActivityHeatmap from "@/components/custom/Portfolio/ActivityHeatmap";
import PrivateModeEditor from "@/components/custom/Portfolio/PrivateModeEditor";
import SkillTimeline from "@/components/custom/Portfolio/SkillTimeline";
import TopProjects from "@/components/custom/Portfolio/TopProjects";

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("private");
  const [featuredIds, setFeaturedIds] = useState(() => new Set());

  // To make the Heatmap (and maybe the skills thing) work well, make the user
  // view it based on the currently clicked on project
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [heatmapRefreshKey, setHeatmapRefreshKey] = useState(0);

  const authHeader = useMemo(() => {
    const token = getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : null;
  }, []);

  useEffect(() => {
    async function generateOrFetchPortfolio() {
      setIsLoading(true);
      setError("");
      if (!authHeader) {
        setError("You must be logged in to view your portfolio.");
        setIsLoading(false);
        return;
      }
      try {
        const res = await axios.post(
          "/api/portfolio/generate",
          {},
          { headers: authHeader },
        );
        console.log("Portfolio projects:", res.data.content?.projects);
        console.log("Full portfolio response:", res.data);
        console.log("Auth header:", authHeader);
        setPortfolio(res.data);
        setFeaturedIds(new Set(
          (res.data.content?.projects ?? []).filter(p => p.is_featured).map(p => p.id)
        ));
      } catch (err) {
        setError(
          err?.response?.data?.detail ||
          err?.message ||
          "Failed to generate portfolio.",
        );
      } finally {
        setIsLoading(false);
      }
    }
    generateOrFetchPortfolio();
  }, [authHeader]);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f8f7f4",
        color: "#1e293b",
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      <style>{`
      * { box-sizing: border-box; }
      .pf-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 1px 4px rgba(15,23,42,0.06); }
      .pf-tag { background: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 6px; padding: 2px 10px; font-size: 11px; color: #0d9488; display: inline-block; font-weight: 500; }
      .pf-mode-btn { padding: 7px 20px; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; border: 1px solid #cbd5e1; background: transparent; color: #64748b; transition: all 0.18s; font-family: inherit; }
      .pf-mode-btn:hover { border-color: #0d9488; color: #0d9488; }
      .pf-mode-btn.active { background: #0d9488; color: #ffffff; border-color: #0d9488; font-weight: 600; }
      .pf-section-title { font-size: 26px; font-weight: 700; text-align: center; color: #0f172a; }
      .pf-divider { width: 44px; height: 3px; background: #0d9488; border-radius: 2px; margin: 10px auto 0; }
      .pf-placeholder { background: #f0fdfa; border: 1px dashed #99f6e4; border-radius: 12px; padding: 36px 24px; }
      .pf-todo-badge { background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); border-radius: 20px; padding: 2px 10px; font-size: 11px; font-weight: 600; color: #d97706; }
    `}</style>

      <Navigation />

      {/* Loading */}
      {isLoading && (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "60vh",
            gap: 16,
          }}
        >
          <Loader2
            style={{ width: 36, height: 36, color: "#0d9488" }}
            className="animate-spin"
          />
          <p style={{ color: "#94a3b8", fontSize: 14 }}>
            Generating your portfolio...
          </p>
        </div>
      )}

      {/* Error */}
      {!isLoading && error && (
        <div style={{ maxWidth: 600, margin: "60px auto", padding: "0 24px" }}>
          <div
            style={{
              background: "#fff1f2",
              border: "1px solid #fecdd3",
              borderRadius: 12,
              padding: "18px 20px",
              display: "flex",
              gap: 12,
              alignItems: "center",
            }}
          >
            <AlertCircle
              style={{ color: "#e11d48", width: 18, height: 18, flexShrink: 0 }}
            />
            <p style={{ color: "#be123c", fontSize: 14, margin: 0 }}>{error}</p>
          </div>
        </div>
      )}

      {!isLoading && !error && portfolio && (
        <>
          {/* ── Hero ── */}
          <div
            style={{
              position: "relative",
              padding: "80px 24px 110px",
              background:
                "linear-gradient(160deg, #f0fdfa 0%, #e6faf7 40%, #f8f7f4 100%)",
              overflow: "hidden",
              borderBottom: "1px solid #e2e8f0",
            }}
          >
            {/* Subtle teal texture blobs */}
            <div
              style={{
                position: "absolute",
                top: -60,
                left: -40,
                width: 380,
                height: 380,
                background:
                  "radial-gradient(circle, rgba(13,148,136,0.07) 0%, transparent 70%)",
                pointerEvents: "none",
              }}
            />
            <div
              style={{
                position: "absolute",
                bottom: 0,
                right: "8%",
                width: 280,
                height: 280,
                background:
                  "radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 70%)",
                pointerEvents: "none",
              }}
            />
            {/* Decorative dot grid */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: "none",
                backgroundImage:
                  "radial-gradient(circle, #cbd5e1 1px, transparent 1px)",
                backgroundSize: "28px 28px",
                opacity: 0.4,
              }}
            />

            <div
              style={{
                maxWidth: 960,
                margin: "0 auto",
                position: "relative",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 48,
                flexWrap: "wrap",
              }}
            >
              {/* Left: text */}
              <div
                style={{
                  flex: 1,
                  minWidth: 260,
                  textAlign: "center",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                }}
              >
                <p
                  style={{
                    color: "#0d9488",
                    fontSize: 13,
                    fontWeight: 600,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    marginBottom: 12,
                  }}
                >
                  Portfolio
                </p>
                <h1
                  style={{
                    fontSize: "clamp(28px, 5vw, 46px)",
                    fontWeight: 700,
                    lineHeight: 1.15,
                    margin: "0 0 16px",
                    fontFamily:
                      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                    color: "#0f172a",
                  }}
                >
                  {portfolio.title || "My Portfolio"}
                </h1>
                {portfolio.summary && (
                  <p
                    style={{
                      color: "#475569",
                      fontSize: 15,
                      lineHeight: 1.75,
                      maxWidth: 460,
                      margin: "0 0 32px",
                      textAlign: "center",
                    }}
                  >
                    {portfolio.summary}
                  </p>
                )}
                {/* Mode toggle */}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
                  <button
                    className={`pf-mode-btn ${mode === "public" ? "active" : ""}`}
                    onClick={() => setMode("public")}
                  >
                    🌐 Public
                  </button>
                  <button
                    className={`pf-mode-btn ${mode === "private" ? "active" : ""}`}
                    onClick={() => setMode("private")}
                  >
                    🔒 Private
                  </button>
                  <button
                    className="pf-mode-btn"
                    onClick={async () => {
                      setIsLoading(true);
                      setError("");
                      try {
                        const res = await axios.post("/api/portfolio/generate", {}, { headers: authHeader });
                        setPortfolio(res.data);
                        setFeaturedIds(new Set(
                          (res.data.content?.projects ?? []).filter(p => p.is_featured).map(p => p.id)
                        ));
                      } catch (err) {
                        setError(err?.response?.data?.detail || err?.message || "Failed to regenerate portfolio.");
                      } finally {
                        setIsLoading(false);
                      }
                    }}
                  >
                    🔄 Refresh
                  </button>
                </div>
              </div>

              {/* Right: stat cards */}
              <div
                style={{ display: "flex", flexDirection: "column", gap: 10 }}
              >
                {[
                  {
                    label: "Projects",
                    value: portfolio.content?.projects?.length ?? 0,
                  },
                  {
                    label: "Skills",
                    value: portfolio.content?.skills?.length ?? "—",
                  },
                  {
                    label: "Languages",
                    value: portfolio.content?.projects
                      ? [
                        ...new Set(
                          portfolio.content.projects.flatMap(
                            (p) => p.languages ?? [],
                          ),
                        ),
                      ].length
                      : "—",
                  },
                ].map(({ label, value }) => (
                  <div
                    key={label}
                    className="pf-card"
                    style={{
                      padding: "14px 28px",
                      textAlign: "center",
                      minWidth: 140,
                    }}
                  >
                    <p
                      style={{
                        fontSize: 26,
                        fontWeight: 700,
                        color: "#0d9488",
                        fontFamily:
                          "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                        margin: 0,
                      }}
                    >
                      {value}
                    </p>
                    <p
                      style={{
                        fontSize: 11,
                        color: "#94a3b8",
                        margin: "4px 0 0",
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                      }}
                    >
                      {label}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom fade to page bg */}
            <div
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                height: 48,
                background: "linear-gradient(to bottom, transparent, #f8f7f4)",
              }}
            />
          </div>

          {/* ── Content ── */}

          {mode === "private" ? (
            <div
              style={{
                maxWidth: 1000,
                margin: "0 auto",
                padding: "64px 24px",
                display: "flex",
                flexDirection: "column",
                gap: 72,
              }}
            >
              <TopProjects
                portfolio={portfolio}
                isPrivate={true}
                featuredIds={featuredIds}
                onFeaturedIdsChange={setFeaturedIds}
                selectedProjectId={selectedProjectId}
                onSelectProject={setSelectedProjectId}
                onSnapshotCreated={(projectId) => {
                  setSelectedProjectId(projectId);
                  setHeatmapRefreshKey((prev) => prev + 1);
                }}
                onPortfolioUpdate={setPortfolio}
              />
              <SkillTimeline />
              <ActivityHeatmap
                projectId={selectedProjectId}
                refreshKey={heatmapRefreshKey}
              />
              <PrivateModeEditor />
            </div>
          ) : (
            <div
              style={{ maxWidth: 1000, margin: "0 auto", padding: "64px 24px", display: "flex", flexDirection: "column", gap: 72 }}
            >
              <TopProjects
                portfolio={portfolio}
                isPrivate={false}
                featuredIds={featuredIds}
                onFeaturedIdsChange={setFeaturedIds}
              />
              <SkillTimeline />
              <ActivityHeatmap
                projectId={selectedProjectId}
                refreshKey={heatmapRefreshKey}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}