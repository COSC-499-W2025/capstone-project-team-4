import { Activity } from "lucide-react";
import { useEffect, useState } from "react";

export default function ActivityHeatmap({ projectId, refreshKey }) {
  const [heatmapData, setHeatmapData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchHeatmap() {
      if (!projectId) {
        setHeatmapData([]);
        setError("");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `/api/snapshots/${projectId}/activity-heatmap`,
        );

        if (!response.ok) {
          throw new Error("Failed to fetch heatmap data");
        }

        const json = await response.json();
        setHeatmapData(json.data ?? []);
      } catch (err) {
        console.error(err);
        setError("Could not load activity heatmap.");
        setHeatmapData([]);
      } finally {
        setLoading(false);
      }
    }

    fetchHeatmap();
  }, [projectId, refreshKey]);

  let content;

  if (!projectId) {
    content = (
      <p style={{ color: "#374151", fontSize: 13, margin: 0, lineHeight: 1.6 }}>
        Select a project to view snapshot activity.
      </p>
    );
  } else if (loading) {
    content = (
      <p style={{ color: "#374151", fontSize: 13, margin: 0, lineHeight: 1.6 }}>
        Loading activity...
      </p>
    );
  } else if (error) {
    content = (
      <p style={{ color: "#b91c1c", fontSize: 13, margin: 0, lineHeight: 1.6 }}>
        {error}
      </p>
    );
  } else if (heatmapData.length === 0) {
    content = (
      <>
        <p
          style={{ color: "#374151", fontSize: 13, margin: 0, lineHeight: 1.6 }}
        >
          Based on snapshots created per day.
        </p>
        <p
          style={{
            color: "#6b7280",
            fontSize: 13,
            marginTop: 8,
            marginBottom: 0,
            lineHeight: 1.6,
          }}
        >
          No snapshot activity yet.
        </p>
      </>
    );
  } else {
    content = (
      <>
        <p
          style={{
            color: "#374151",
            fontSize: 13,
            marginTop: 0,
            marginBottom: 12,
            lineHeight: 1.6,
          }}
        >
          Based on snapshots created per day.
        </p>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: 8,
            marginTop: 12,
          }}
        >
          {heatmapData.map((day) => (
            <div
              key={day.date}
              title={`${day.date}: ${day.count} snapshot${day.count === 1 ? "" : "s"}`}
              style={{
                width: 20,
                height: 20,
                borderRadius: 4,
                background:
                  day.count === 0
                    ? "#e5e7eb"
                    : day.count === 1
                      ? "#bfdbfe"
                      : day.count <= 3
                        ? "#60a5fa"
                        : "#2563eb",
              }}
            />
          ))}
        </div>
      </>
    );
  }

  return (
    <section>
      <h2 className="pf-section-title">Activity</h2>
      <div className="pf-divider" />

      <div
        className="pf-placeholder"
        style={{ marginTop: 32, textAlign: "center" }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 10,
            marginBottom: 12,
          }}
        >
          <Activity style={{ width: 20, height: 20, color: "#4b5563" }} />
          <h3
            style={{
              color: "#4b5563",
              fontSize: 15,
              fontWeight: 600,
              margin: 0,
            }}
          >
            Snapshot Activity Heatmap
          </h3>
        </div>

        {content}
      </div>
    </section>
  );
}
