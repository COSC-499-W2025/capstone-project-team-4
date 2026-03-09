import { getAccessToken } from "@/lib/auth";
import axios from "axios";

function getAuthConfig() {
    const token = getAccessToken();

    return token
        ? {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
        : {};
}

export async function getMyProfile() {
    try {
        const response = await axios.get("/api/user-profiles/me", getAuthConfig());
        return response.data;
    } catch (err) {
        const status = err?.response?.status;
        const detail =
            err?.response?.data?.detail ||
            err?.message ||
            "Failed to load profile.";

        const error = new Error(
            typeof detail === "string" ? detail : "Failed to load profile."
        );
        error.status = status;
        throw error;
    }
}

export async function upsertMyProfile(data) {
    try {
        const response = await axios.put(
            "/api/user-profiles/me",
            data,
            getAuthConfig()
        );
        return response.data;
    } catch (err) {
        const status = err?.response?.status;
        const detail =
            err?.response?.data?.detail ||
            err?.message ||
            "Failed to save profile.";

        const error = new Error(
            typeof detail === "string" ? detail : "Failed to save profile."
        );
        error.status = status;
        throw error;
    }
}