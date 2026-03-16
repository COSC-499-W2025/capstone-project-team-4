export function buildSkillSnapshots(projects, timelineResponses) {
  const projectMetaById = new Map(
    projects.map((project) => [
      project.project_id ?? project.id,
      {
        projectId: project.project_id ?? project.id,
        projectName: project.name,
        createdAt: project.created_at,
      },
    ])
  );

  const snapshots = [];

  for (const response of timelineResponses) {
    if (!response || !Array.isArray(response.timeline)) continue;

    const projectId = response.project_id;
    const projectMeta = projectMetaById.get(projectId);

    if (!projectMeta) continue;

    const skillsMap = new Map();

    for (const entry of response.timeline) {
      const { skill, count = 1 } = entry;
      if (!skill) continue;

      if (!skillsMap.has(skill)) {
        skillsMap.set(skill, {
          skill,
          count: 0,
        });
      }

      const skillRecord = skillsMap.get(skill);
      skillRecord.count += count;
    }

    snapshots.push({
      projectId: projectMeta.projectId,
      projectName: projectMeta.projectName,
      createdAt: projectMeta.createdAt,
      skills: [...skillsMap.values()].sort((a, b) => {
        if (b.count !== a.count) return b.count - a.count;
        return a.skill.localeCompare(b.skill);
      }),
    });
  }

  return snapshots.sort(
    (a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0)
  );
}