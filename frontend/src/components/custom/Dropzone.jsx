import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { File, X, FolderArchive } from "lucide-react";
import axios from "axios";

export default function Dropzone({ title = "" }) {
  // 1. We manage the files ourselves now (so we can delete them)
  const [files, setFiles] = useState([]);

  const onDrop = useCallback((acceptedFiles) => {
    // Appending new files to existing ones (instead of replacing)
    setFiles((prev) => [...prev, ...acceptedFiles]);
  }, []);

  function removeFile(fileToRemove) {
    setFiles((prev) => prev.filter((f) => f !== fileToRemove));
  }

  function removeAll() {
    setFiles([]);
  }

  function submitFiles() {
    if (files.length !== 0) {
      const formData = new FormData();

      files.forEach((file) => {
        // For some reason in the api it's called file? In any case, just keep file for now.. otherwise it'll error
        formData.append("file", file);
      });

      axios
        .post("http://127.0.0.1:8000/api/projects/analyze/upload", formData)
        .then((response) => console.log("Success!", response))
        .catch((error) => console.error("Error", error));
    } else {
      return;
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    // For now, only take zip files
    accept: {
      "application/zip": [".zip"],
      "application/x-zip-compressed": [".zip"],
    },
    onDrop,
  });

  return (
    <section className="container max-w-xl mx-auto space-y-6">
      <h2>{title}</h2>
      {/* Drop zone */}
      <Card
        {...getRootProps()}
        className={`
                    border-2 border-dashed cursor-pointer transition-colors
                    ${isDragActive ? "border-primary bg-primary/10" : "border-muted-foreground/25 hover:bg-muted/50"}
                `}
      >
        <CardContent className="flex flex-col items-center justify-center h-40 text-center space-y-2 pt-6">
          <input {...getInputProps()} />
          <p className="text-sm font-medium text-muted-foreground">
            {isDragActive
              ? "Drop files (or folders) here!"
              : "Drag & drop .zip files here"}
          </p>
        </CardContent>
      </Card>

      {/* FILE LIST WITH 'X' BUTTON for deleting */}
      {files.length > 0 && (
        <aside className="space-y-3 flex flex-col gap-3">
          <h4 className="text-sm font-medium text-muted-foreground">
            Files ({files.length})
          </h4>
          <ScrollArea className="h-[250px] w-full rounded-md border p-4">
            <div className="space-y-2">
              {files.map((file, index) => (
                <div
                  key={`${file.path}-${index}`}
                  className="flex items-center justify-between p-3 border rounded-lg shadow-sm bg-card text-card-foreground"
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    {/* Show .zip icon if it's a zip, else file icon cause uh... yeah why not?*/}
                    <div className="p-2 bg-muted rounded-md">
                      {file.type.includes("zip") ||
                      file.name.endsWith(".zip") ? (
                        <FolderArchive className="w-4 h-4 text-orange-500" />
                      ) : (
                        <File className="w-4 h-4 text-blue-500" />
                      )}
                    </div>
                    <div className="flex flex-col truncate">
                      <span className="text-sm font-medium truncate max-w-[200px]">
                        {file.path || file.name}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {(file.size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                  </div>

                  {/* THE X BUTTON */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-red-500 hover:bg-red-50"
                    onClick={() => removeFile(file)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </ScrollArea>
          {/* The 2 buttons */}

          <div className="flex justify-center gap-8">
            <Button
              size="lg"
              className="text-lg px-8 hover:cursor-pointer"
              type="button"
              onClick={removeAll}
            >
              Delete all
            </Button>

            <Button
              size="lg"
              className="text-lg px-8 hover:cursor-pointer"
              type="button"
              onClick={submitFiles}
            >
              Analyze Project
            </Button>
          </div>
        </aside>
      )}
    </section>
  );
}
