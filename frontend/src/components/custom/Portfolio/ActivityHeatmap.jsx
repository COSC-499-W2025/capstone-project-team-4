import { Activity } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ActivityCalendar } from "react-activity-calendar";

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

  const calendarData = useMemo(() => {
    const dateMap = new Map(heatmapData.map((day) => [day.date, day.count]));

    const year = new Date().getFullYear();
    const start = new Date(year, 0, 1);
    const end = new Date(year, 11, 31);

    const filledData = [];

    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split("T")[0];
      const count = dateMap.get(dateStr) ?? 0;

      filledData.push({
        date: dateStr,
        count,
        level:
          count === 0
            ? 0
            : count === 1
              ? 1
              : count <= 3
                ? 2
                : count <= 5
                  ? 3
                  : 4,
      });
    }

    return filledData;
  }, [heatmapData]);

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
          style={{ display: "flex", justifyContent: "center", marginTop: 12 }}
        >
          <ActivityCalendar
            data={calendarData}
            maxLevel={4}
            blockSize={16}
            blockMargin={6}
            fontSize={12}
            theme={{
              light: ["#e5e7eb", "#bfdbfe", "#93c5fd", "#60a5fa", "#2563eb"],
              dark: ["#e5e7eb", "#bfdbfe", "#93c5fd", "#60a5fa", "#2563eb"],
            }}
            labels={{
              totalCount: "{{count}} activities in {{year}}",
            }}
          />
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
