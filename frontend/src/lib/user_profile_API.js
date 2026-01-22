import apiClient from "./Client_API";

// GET user profiles
export function listProfiles({ page = 1, page_size = 20 } = {}) {
    return apiClient
        .get("/api/user-profiles", {
            params: { page, page_size },
        })
        .then((response) => {
            return response.data;
        })
        .catch((error) => {
            console.error("Failed to fetch user profiles:", error);
        });
}

// POST - To be implemented once parameters are added
