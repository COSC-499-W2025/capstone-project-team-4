import CTA from "@/components/custom/CTA";
import Dropzone from "@/components/custom/Dropzone";
import { useAnalyzeProject } from "@/hooks/useAnalyzeProject";
import { useMemo, useState } from "react";

const MODES = [
    { key: "zip", label: "Upload ZIP" },
    { key: "github", label: "GitHub Repo" },
    { key: "directory", label: "Local Directory" },
];

export default function AnalyzeProject() {
    const { status, data, error, run, reset } = useAnalyzeProject();
    const [mode, setMode] = useState("zip");
    // ZIP
    const [files, setFiles] = useState([]);
    const [zipProjectName, setZipProjectName] = useState("");
    // GitHub
    const [githubUrl, setGithubUrl] = useState("");
    const [branch, setBranch] = useState("");
    // Directory
    const [directoryPath, setDirectoryPath] = useState("");
    const [dirProjectName, setDirProjectName] = useState("");
    const zipFile = useMemo(() => files?.[0] ?? null, [files]);

    const canRun =
        status !== "running" &&
        ((mode === "zip" && !!zipFile) ||
        (mode === "github" && githubUrl.trim().length > 0) ||
        (mode === "directory" && directoryPath.trim().length > 0));

    const onAnalyze = async () => {
        if (mode === "zip") {
        await run("zip", { file: zipFile, project_name: zipProjectName });
        } else if (mode === "github") {
        await run("github", { github_url: githubUrl, branch });
        } else if (mode === "directory") {
        await run("directory", { directory_path: directoryPath, project_name: dirProjectName });
        }
    };

    return (
        <div className="mx-auto max-w-4xl space-y-6 px-5 py-10">
        <h1 className="text-2xl font-semibold text-white">Analyze Project</h1>

        <div className="flex flex-wrap gap-2">
            {MODES.map((m) => (
            <button
                key={m.key}
                type="button"
                onClick={() => {
                setMode(m.key);
                reset();
                }}
                className={[
                "rounded-full border px-4 py-2 text-sm transition",
                mode === m.key
                    ? "border-white/20 bg-white/10 text-white"
                    : "border-white/10 bg-white/5 text-neutral-300 hover:bg-white/10",
                ].join(" ")}
            >
                {m.label}
            </button>
            ))}
        </div>

        {mode === "zip" && (
            <div className="space-y-3">
            <Dropzone title="Upload ZIP Folder" onFilesChange={setFiles} />
            <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.25em] text-neutral-400">
                Optional Project Name
                </label>
                <input
                value={zipProjectName}
                onChange={(e) => setZipProjectName(e.target.value)}
                placeholder="e.g., Capstone"
                className="h-11 w-full rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-white outline-none"
                />
            </div>
            </div>
        )}

        {mode === "github" && (
            <div className="space-y-3">
            <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.25em] text-neutral-400">
                GitHub Repo URL (public only)
                </label>
                <input
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="h-11 w-full rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-white outline-none"
                />
            </div>

            <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.25em] text-neutral-400">
                Optional Branch
                </label>
                <input
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="main"
                className="h-11 w-full rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-white outline-none"
                />
            </div>
            </div>
        )}

        {mode === "directory" && (
            <div className="space-y-3">
            <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.25em] text-neutral-400">
                Absolute Directory Path (local/dev)
                </label>
                <input
                value={directoryPath}
                onChange={(e) => setDirectoryPath(e.target.value)}
                placeholder="/Users/kusshsatija/Desktop/my-project"
                className="h-11 w-full rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-white outline-none"
                />
            </div>

            <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.25em] text-neutral-400">
                Optional Project Name
                </label>
                <input
                value={dirProjectName}
                onChange={(e) => setDirProjectName(e.target.value)}
                placeholder="e.g., Courtsy"
                className="h-11 w-full rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-white outline-none"
                />
            </div>

            <p className="text-xs text-neutral-400">
                Backend must run on the same machine and have permission to read that path.
            </p>
            </div>
        )}

        <div className="flex items-center gap-3">
            <CTA onClick={onAnalyze} disabled={!canRun}>
            {status === "running" ? "Analyzing..." : "Analyze"}
            </CTA>

            <button
            type="button"
            onClick={reset}
            className="text-sm text-neutral-400 hover:text-white"
            >
            Reset
            </button>
        </div>

        {status === "error" && (
            <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">
            {error?.response?.data ? JSON.stringify(error.response.data) : String(error)}
            </div>
        )}

        {status === "success" && data && (
            <pre className="max-h-[520px] overflow-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-xs text-neutral-200">
    {JSON.stringify(data, null, 2)}
            </pre>
        )}
        </div>
    );
}
