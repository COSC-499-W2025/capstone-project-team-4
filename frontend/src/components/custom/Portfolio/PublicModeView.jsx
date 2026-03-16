import { Globe, Search } from "lucide-react";

export default function ActivityHeatmap() {
  return (
    <section>
      <h2 className="pf-section-title">Public View</h2>
      <div className="pf-divider" />

      <div className="pf-placeholder" style={{ marginTop: 32, textAlign: "center" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 12 }}>
          <Globe style={{ width: 20, height: 20, color: "#4b5563" }} />
          <h3 style={{ color: "#4b5563", fontSize: 15, fontWeight: 600, margin: 0 }}>Read-only portfolio with search & filter</h3>
          <span className="pf-todo-badge">TODO</span>
        </div>
        <p style={{ color: "#374151", fontSize: 13, margin: 0, lineHeight: 1.6 }}>
          Endpoint: <code style={{ color: "#6b7280" }}>GET /portfolio/&#123;id&#125;</code> (no auth required)
          <br />Search and filter are frontend-only — filter projects by name, language, or framework
        </p>
      </div>
    </section>
  );
}
