const ACCESS_TOKEN_KEY = "access_token";
const GENERATOR_CACHE_KEYS = ["uploadedFiles", "projectData", "consentGiven"];

function clearGeneratorCache() {
  for (const key of GENERATOR_CACHE_KEYS) {
    localStorage.removeItem(key);
  }
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token) {
  // Reset generator cache so data from a previous account cannot leak after login.
  clearGeneratorCache();
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  // Clear per-browser cached generator data on logout as well.
  clearGeneratorCache();
}

export function isAuthenticated() {
  return Boolean(getAccessToken());
}
