import axios from "axios";

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000",
    headers: {
        Accept: "application/json",
    },
    timeout: 30000,
});

// Centralized error logging
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error("API error:", error?.response ?? error);
        return Promise.reject(error);
    }
);

export default apiClient;
