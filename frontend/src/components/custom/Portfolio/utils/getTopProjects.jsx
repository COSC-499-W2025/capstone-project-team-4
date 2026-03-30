export function getTopProjects(projectsInput) {
    const projects = Array.isArray(projectsInput) ? projectsInput : [];

    return [...projects]
        .sort((a, b) => (b.total_lines_of_code || 0) - (a.total_lines_of_code || 0))
        .slice(0, 3);
}
