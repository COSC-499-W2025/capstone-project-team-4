import { TrendingUp } from "lucide-react";

export default function SkillTimeline() {
  return (
    <section>
      <h2 className="pf-section-title">Skills Timeline</h2>
      <div className="pf-divider" />

      <div className="pf-placeholder" style={{ marginTop: 32, textAlign: "center" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 12 }}>
          <TrendingUp style={{ width: 20, height: 20, color: "#4b5563" }} />
          <h3 style={{ color: "#4b5563", fontSize: 15, fontWeight: 600, margin: 0 }}>Timeline of skill progression</h3>
        </div>
        <p style={{ color: "#374151", fontSize: 13, margin: 0, lineHeight: 1.6 }}>
          <br />Call per project, merge by date, render as AreaChart
        </p>
      </div>
    </section>
  );
}
