// src/hooks/useAnalyzeProject.js
import { useCallback, useState } from "react";
import {
    analyzeProjectDirectory,
    analyzeProjectGithub,
    analyzeProjectUploadZip,
} from "../lib/analysis_API";

export function useAnalyzeProject() {
    const [status, setStatus] = useState("idle"); // idle | running | success | error
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    const reset = useCallback(() => {
        setStatus("idle");
        setData(null);
        setError(null);
    }, []);

    const run = useCallback(async (mode, payload) => {
        setStatus("running");
        setData(null);
        setError(null);

        try {
        let result;

        if (mode === "zip") {
            result = await analyzeProjectUploadZip(payload.file, payload.project_name);
        } else if (mode === "github") {
            result = await analyzeProjectGithub({
            github_url: payload.github_url,
            branch: payload.branch,
            });
        } else if (mode === "directory") {
            result = await analyzeProjectDirectory({
            directory_path: payload.directory_path,
            project_name: payload.project_name,
            });
        } else {
            throw new Error(`Unknown mode: ${mode}`);
        }

        setData(result);
        setStatus("success");
        return result;
        } catch (e) {
        setError(e);
        setStatus("error");
        throw e;
        }
    }, []);

    return { status, data, error, run, reset };
}
