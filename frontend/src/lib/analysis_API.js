// src/lib/analysis_API.js
import apiClient from "./Client_API";

/**
 * 1) Upload ZIP (multipart/form-data)
 * Backend: POST /api/projects/analyze/upload
 * Body: file (binary), project_name (optional)
 */
export async function analyzeProjectUploadZip(file, projectName) {
    if (!file) throw new Error("No ZIP file provided");

    const formData = new FormData();
    formData.append("file", file);

    if (projectName && projectName.trim()) {
        formData.append("project_name", projectName.trim());
    }

    const res = await apiClient.post("/api/projects/analyze/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 300000,
    });

    return res.data;
}

/**
 * 2) GitHub repo (JSON)
 * Backend: POST /api/projects/analyze/github
 * Body: { github_url, branch? }
 */
export async function analyzeProjectGithub({ github_url, branch }) {
    if (!github_url || !github_url.trim()) throw new Error("GitHub URL is required");

    const payload = {
        github_url: github_url.trim(),
        ...(branch && branch.trim() ? { branch: branch.trim() } : {}),
    };

    const res = await apiClient.post("/api/projects/analyze/github", payload, {
        headers: { "Content-Type": "application/json" },
        timeout: 300000,
    });

    return res.data;
}

/**
 * 3) Local directory absolute path (JSON)
 * Backend: POST /api/projects/analyze/directory
 * Body: { directory_path, project_name? }
 */
export async function analyzeProjectDirectory({ directory_path, project_name }) {
    if (!directory_path || !directory_path.trim()) {
        throw new Error("Directory absolute path is required");
    }

    const payload = {
        directory_path: directory_path.trim(),
        ...(project_name && project_name.trim() ? { project_name: project_name.trim() } : {}),
    };

    const res = await apiClient.post("/api/projects/analyze/directory", payload, {
        headers: { "Content-Type": "application/json" },
        timeout: 300000,
    });

    return res.data;
}
