import { Activity } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ActivityCalendar } from "react-activity-calendar";

function toDateString(value) {
  const date = new Date(value);
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getLevel(count) {
  if (count === 0) return 0;
  if (count === 1) return 1;
  if (count <= 3) return 2;
  if (count <= 5) return 3;
  return 4;
}

export default function ActivityHeatmap({ projectId, contributorIdentity }) {
  const [heatmapData, setHeatmapData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [projectName, setProjectName] = useState("");

  useEffect(() => {
    async function fetchHeatmap() {
      if (!projectId || !contributorIdentity) {
        setHeatmapData([]);
        setError("");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `/api/contributors/github/${encodeURIComponent(contributorIdentity)}/projects/${projectId}/activity-heatmap`,
        );

        if (response.status === 404) {
          setHeatmapData([]);
          setError("");
          return;
        }

        if (!response.ok) {
          throw new Error("Failed to fetch heatmap data");
        }

        const json = await response.json();
        setHeatmapData(json.data ?? []);
      } catch (err) {
        console.error(err);
        setError("Could not load commit activity.");
        setHeatmapData([]);
      } finally {
        setLoading(false);
      }
    }

    async function getProjectName() {
      if (!projectId) {
        setError("");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/projects/${projectId}`);
        const project = await response.json();
        setProjectName(project.name);
      } catch (error) {
        console.error(error);
      }
    }

    fetchHeatmap();
    getProjectName();
  }, [projectId, contributorIdentity]);

  function formatTooltip(activity) {
    const formattedDate = new Date(
      `${activity.date}T00:00:00`,
    ).toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });

    const commitText =
      activity.count === 1 ? "1 commit" : `${activity.count} commits`;

    return `${commitText} on ${formattedDate}`;
  }

  const calendarData = useMemo(() => {
    const today = new Date();
    const start = new Date(today);
    start.setDate(today.getDate() - 364);

    const dateMap = new Map(
      heatmapData.map((day) => [day.date, Number(day.count) || 0]),
    );

    const filledData = [];
    const cursor = new Date(start);

    while (cursor <= today) {
      const dateStr = toDateString(cursor);
      const count = dateMap.get(dateStr) ?? 0;

      filledData.push({
        date: dateStr,
        count,
        level: getLevel(count),
      });

      cursor.setDate(cursor.getDate() + 1);
    }

    return filledData;
  }, [heatmapData]);

  let content;

  if (!projectId) {
    content = (
      <p className="text-gray-500 text-sm/1.6 m-0">
        Select a project to view commit activity.
      </p>
    );
  } else if (loading) {
    content = (
      <p className="text-gray-500 text-sm/1.6 m-0">Loading activity...</p>
    );
  } else if (error) {
    content = <p className="text-red-500 text-sm/1.6 m-0">{error}</p>;
  } else if (heatmapData.length === 0) {
    content = (
      <>
        <p className="text-gray-500 text-sm/1.6 m-0">
          Based on commits grouped by day for the selected project.
        </p>
        <strong className="font-bold">
          It's a solo project or there are no matched commits yet.
        </strong>
      </>
    );
  } else {
    content = (
      <>
        <strong>Viewing Project: {projectName}</strong>
        <p className="text-gray-500 text-sm/1.6 mt-0 mb-8">
          Based on commits grouped by day for the selected project.
        </p>

        <div className="flex justify-center">
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
              totalCount: "{{count}} commits in the last year",
            }}
            tooltips={{
              activity: {
                text: (activity) => formatTooltip(activity),
                placement: "right",
              },
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

      <div className="pf-placeholder mt-8 text-center">
        <div className="flex items-center justify-center gap-4 mb-2">
          <Activity height={20} width={20} />
          <h3 className="gray-800 font-medium">Commit Activity Heatmap</h3>
        </div>

        {content}
      </div>
    </section>
  );
}
