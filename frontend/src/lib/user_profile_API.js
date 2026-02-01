    // src/lib/user_profile_API.js

    const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5173/";
    const API_PREFIX = "/api";

    async function handle(res) {
    if (!res.ok) {
        const text = await res.text().catch(() => "");
        const err = new Error(text || `Request failed (${res.status})`);
        err.status = res.status;
        throw err;
    }
    if (res.status === 204) return null;
    return res.json();
    }

export function listProfiles({ page = 1, page_size = 20 } = {}) {
const url = new URL(`${API_BASE}${API_PREFIX}/user-profiles`);
url.searchParams.set("page", String(page));
url.searchParams.set("page_size", String(page_size));

return fetch(url.toString(), {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        // credentials: "", "include" for cookies, "Authorication" for bearer token
    }).then(handle);
}

export function getProfileByUserId(userId) {
    return fetch(`${API_BASE}${API_PREFIX}/user-profiles/user/${userId}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        // credentials: "", "include" for cookies, "Authorication" for bearer token
    }).then(handle);
}

export function createProfile(userId, payload) {
    return fetch(`${API_BASE}${API_PREFIX}/user-profiles/user/${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // credentials: "", "include" for cookies, "Authorication" for bearer token
        body: JSON.stringify(payload),
    }).then(handle);
}

export function updateProfile(userId, payload) {
    return fetch(`${API_BASE}${API_PREFIX}/user-profiles/user/${userId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        // credentials: "", "include" for cookies, "Authorication" for bearer token
        body: JSON.stringify(payload),
    }).then(handle);
}

export function deleteProfile(userId) {
    return fetch(`${API_BASE}${API_PREFIX}/user-profiles/user/${userId}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        // credentials: "", "include" for cookies, "Authorication" for bearer token
    }).then(handle);
}
