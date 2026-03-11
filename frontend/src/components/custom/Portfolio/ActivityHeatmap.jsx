import { Activity } from "lucide-react";

export default function ActivityHeatmap({ portfolio }) {
  return (
    <section>
      <h2 className="pf-section-title">Activity</h2>
      <div className="pf-divider" />

      <div className="pf-placeholder" style={{ marginTop: 32, textAlign: "center" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 12 }}>
          <Activity style={{ width: 20, height: 20, color: "#4b5563" }} />
          <h3 style={{ color: "#4b5563", fontSize: 15, fontWeight: 600, margin: 0 }}>Heatmap of project activity</h3>
        </div>
        <p style={{ color: "#374151", fontSize: 13, margin: 0, lineHeight: 1.6 }}>
        </p>
      </div>
    </section>
  );
}
