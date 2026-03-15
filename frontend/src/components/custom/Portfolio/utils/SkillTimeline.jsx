export function formatTimelineDate(dateString) {
  const date = new Date(`${dateString}T00:00:00`);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function mergeSkillTimelines(projects, timelineResponses) {
  const projectNameById = new Map(
    projects.map((project) => [project.project_id ?? project.id, project.name])
  );

  const groupedByDate = new Map();

  for (const response of timelineResponses) {
    if (!response || !Array.isArray(response.timeline)) continue;

    const projectId = response.project_id;
    const projectName = projectNameById.get(projectId) || `Project ${projectId}`;

    for (const entry of response.timeline) {
      const { skill, date, count = 1 } = entry;
      if (!skill || !date) continue;

      if (!groupedByDate.has(date)) {
        groupedByDate.set(date, new Map());
      }

      const skillsMap = groupedByDate.get(date);

      if (!skillsMap.has(skill)) {
        skillsMap.set(skill, {
          skill,
          totalCount: 0,
          projectCount: 0,
          projects: [],
        });
      }

      const skillRecord = skillsMap.get(skill);
      skillRecord.totalCount += count;

      const existingProject = skillRecord.projects.find(
        (project) => project.projectId === projectId
      );

      if (existingProject) {
        existingProject.count += count;
      } else {
        skillRecord.projects.push({
          projectId,
          projectName,
          count,
        });
      }

      skillRecord.projectCount = skillRecord.projects.length;
    }
  }

  return [...groupedByDate.entries()]
    .map(([date, skillsMap]) => ({
      date,
      formattedDate: formatTimelineDate(date),
      skills: [...skillsMap.values()].sort((a, b) => {
        if (b.projectCount !== a.projectCount) {
          return b.projectCount - a.projectCount;
        }
        return a.skill.localeCompare(b.skill);
      }),
    }))
    .sort((a, b) => new Date(b.date) - new Date(a.date));
}
