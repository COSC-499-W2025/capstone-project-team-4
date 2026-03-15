import axios from 'axios';
import { getAccessToken } from '@/lib/auth';

function authConfig() {
  const token = getAccessToken();
  return token ? { headers: { Authorization: `Bearer ${token}` } } : {};
}

/** GET /api/user-profiles/me → UserProfileDetail (includes user_id, name, phone, etc.) */
export async function getMyProfile() {
  const res = await axios.get('/api/user-profiles/me', authConfig());
  return res.data;
}

/** GET /api/users/{userId}/resume → FullResumeData */
export async function getUserResume(userId) {
  const res = await axios.get(`/api/users/${userId}/resume`, authConfig());
  return res.data;
}

/** GET /api/projects?page=1&page_size=50 → ProjectList */
export async function listProjects(page = 1, pageSize = 50) {
  const res = await axios.get(`/api/projects?page=${page}&page_size=${pageSize}`, authConfig());
  return res.data;
}

/** GET /api/projects/{projectId}/resume/latest → ResumeItemSchema */
export async function getProjectResumeLatest(projectId) {
  const res = await axios.get(`/api/projects/${projectId}/resume/latest`, authConfig());
  return res.data;
}

/** GET /api/projects/{projectId}/skills/sources → SkillSourceResponse */
export async function getProjectSkillSources(projectId) {
  const res = await axios.get(`/api/projects/${projectId}/skills/sources`, authConfig());
  return res.data;
}

/**
 * POST /api/projects/analyze/upload (multipart/form-data) → List[AnalysisResult]
 * @param {File} file  ZIP file to upload
 * @param {string} projectName  Optional custom project name
 */
export async function analyzeZipUpload(file, projectName = '') {
  const token = getAccessToken();
  const form = new FormData();
  form.append('file', file);
  if (projectName) form.append('project_name', projectName);
  const res = await axios.post('/api/projects/analyze/upload', form, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return res.data; // List[AnalysisResult]
}

/**
 * POST /api/projects/analyze/github → AnalysisResult | List[AnalysisResult]
 * Always normalised to a List by this function.
 */
export async function analyzeGitHubUrl(githubUrl, branch = null) {
  const body = { github_url: githubUrl };
  if (branch) body.branch = branch;
  const res = await axios.post('/api/projects/analyze/github', body, authConfig());
  const data = res.data;
  return Array.isArray(data) ? data : [data];
}
