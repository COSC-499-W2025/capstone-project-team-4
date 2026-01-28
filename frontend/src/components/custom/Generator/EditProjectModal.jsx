// EditProjectModal.jsx
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Calendar, FileText, Plus, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

function Field({ label, hint, children, className = "" }) {
  return (
    <div className={["space-y-2", className].join(" ")}>
      <div className="flex items-end justify-between gap-3">
        <Label className="text-sm font-medium">{label}</Label>
        {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
      </div>
      {children}
    </div>
  );
}

function SectionHeader({ title, description, icon: Icon }) {
  return (
    <div className="flex items-start gap-3">
      {Icon ? (
        <div className="mt-0.5 grid h-9 w-9 place-items-center rounded-lg border bg-background">
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
      ) : null}
      <div className="min-w-0">
        <p className="text-sm font-semibold leading-none">{title}</p>
        {description ? (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        ) : null}
      </div>
    </div>
  );
}

/**
 * ChipInput
 * - Enter to add
 * - Deduped + trimmed
 * - Responsive layout (stack on mobile)
 * - Accessible remove buttons
 */
function ChipInput({
  label,
  placeholder,
  value,
  setValue,
  items,
  setItems,
  badgeVariant = "secondary",
  badgeClassName = "",
}) {
  const add = () => {
    const v = value.trim();
    if (!v) return;

    const exists = (items ?? []).some((x) => x.toLowerCase() === v.toLowerCase());
    if (exists) {
      setValue("");
      return;
    }
    setItems([...(items ?? []), v]);
    setValue("");
  };

  const remove = (index) => {
    setItems((items ?? []).filter((_, i) => i !== index));
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      add();
    }
  };

  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium">{label}</Label>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          className="sm:flex-1"
        />
        <Button
          type="button"
          onClick={add}
          className="w-full sm:w-auto"
          variant="secondary"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add
        </Button>
      </div>

      {(items ?? []).length ? (
        <div className="flex flex-wrap gap-2 pt-1">
          {(items ?? []).map((item, index) => (
            <Badge
              key={`${item}-${index}`}
              variant={badgeVariant}
              className={[
                "group inline-flex items-center gap-1.5 pr-1.5",
                badgeClassName,
              ].join(" ")}
            >
              <span className="max-w-[18rem] truncate">{item}</span>
              <button
                type="button"
                onClick={() => remove(index)}
                aria-label={`Remove ${item}`}
                className="rounded-sm p-1 text-muted-foreground transition hover:text-destructive focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </Badge>
          ))}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">
          Add items with <span className="font-medium">Enter</span> or the Add button.
        </p>
      )}
    </div>
  );
}

const toDateInput = (d) => {
  if (!d) return "";
  const dt = new Date(d);
  if (Number.isNaN(dt.getTime())) return "";
  return dt.toISOString().split("T")[0];
};

const todayInput = () => new Date().toISOString().split("T")[0];

const EditProjectModal = ({ isOpen, onClose, project, onSave }) => {
  const initial = useMemo(
    () => ({
      name: project?.name || "",
      contributions: project?.contributions || 0,
      date: project?.date ? toDateInput(project.date) : todayInput(),
      projectStartedAt: project?.projectStartedAt
        ? toDateInput(project.projectStartedAt)
        : "",
      description: project?.description || "",
      languages: project?.languages || [],
      frameworks: project?.frameworks || [],
      skills: project?.skills || [],
      toolsAndTechnologies: project?.toolsAndTechnologies || [],
    }),
    [project]
  );

  const [formData, setFormData] = useState(initial);

  // local chip inputs
  const [newLanguage, setNewLanguage] = useState("");
  const [newFramework, setNewFramework] = useState("");
  const [newSkill, setNewSkill] = useState("");
  const [newTool, setNewTool] = useState("");

  // reset form when opening OR switching projects
  useEffect(() => {
    if (!isOpen) return;
    setFormData(initial);
    setNewLanguage("");
    setNewFramework("");
    setNewSkill("");
    setNewTool("");
  }, [isOpen, initial]);

  const setField = (name, value) => {
    setFormData((prev) => ({
      ...prev,
      [name]:
        name === "contributions"
          ? Math.max(0, parseInt(value, 10) || 0)
          : value,
    }));
  };

  const handleSave = () => {
    const updatedData = {
      ...formData,
      date: new Date(formData.date || todayInput()).toISOString(),
      projectStartedAt: formData.projectStartedAt
        ? new Date(formData.projectStartedAt).toISOString()
        : null,
    };
    onSave(updatedData);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        className={[
          "w-[calc(100vw-1.5rem)] sm:w-full",
          "max-w-3xl",
          "max-h-[85vh] sm:max-h-[90vh]",
          "overflow-hidden p-0",
        ].join(" ")}
      >
        {/* Header */}
        <div className="border-b px-5 py-4 sm:px-6">
          <DialogHeader>
            <DialogTitle className="text-base sm:text-lg">
              Edit Project Details
            </DialogTitle>
            <DialogDescription className="text-sm">
              Update the details that will be used in your resume + insights.
            </DialogDescription>
          </DialogHeader>
        </div>

        {/* Body (scrollable) */}
        <div className="max-h-[calc(85vh-9.5rem)] sm:max-h-[calc(90vh-10rem)] overflow-y-auto px-5 py-5 sm:px-6">
          <div className="space-y-8">
            {/* Core */}
            <div className="space-y-4">
              <SectionHeader
                title="Core details"
                description="Abstract level fields."
                icon={FileText}
              />

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Project Name">
                  <Input
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={(e) => setField("name", e.target.value)}
                    placeholder="My Awesome Project"
                  />
                </Field>

                <Field label="Files Analyzed">
                  <Input
                    id="contributions"
                    name="contributions"
                    type="number"
                    inputMode="numeric"
                    min={0}
                    value={formData.contributions}
                    onChange={(e) => setField("contributions", e.target.value)}
                    placeholder="0"
                  />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Project Start Date">
                  <div className="relative">
                    <Calendar className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="projectStartedAt"
                      name="projectStartedAt"
                      type="date"
                      value={formData.projectStartedAt}
                      onChange={(e) =>
                        setField("projectStartedAt", e.target.value)
                      }
                      className="pl-9"
                    />
                  </div>
                </Field>

                <Field label="Analyzed Date">
                  <div className="relative">
                    <Calendar className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="date"
                      name="date"
                      type="date"
                      value={formData.date}
                      onChange={(e) => setField("date", e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </Field>
              </div>

              <Field
                label="Description"
                hint={`${(formData.description || "").length}/300`}
              >
                <Textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={(e) => {
                    const v = e.target.value.slice(0, 300);
                    setField("description", v);
                  }}
                  placeholder="What it does, who it helps, and any standout results…"
                  rows={4}
                  className="resize-none"
                />
              </Field>
            </div>

            {/* Tags */}
            <div className="space-y-4">
              <SectionHeader
                title="Expanded details"
                description="These fields are used for resume building."
                icon={Plus}
              />

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* Languages → Blue */}
                <ChipInput
                  label="Languages"
                  placeholder="Add a language (e.g., Python)"
                  value={newLanguage}
                  setValue={setNewLanguage}
                  items={formData.languages}
                  setItems={(arr) =>
                    setFormData((p) => ({ ...p, languages: arr }))
                  }
                  badgeVariant="secondary"
                  badgeClassName="
                    bg-blue-500/10 text-blue-700 border border-blue-500/20
                    dark:bg-blue-400/10 dark:text-blue-300 dark:border-blue-400/20
                  "
                />

                {/* Frameworks → Purple */}
                <ChipInput
                  label="Frameworks"
                  placeholder="Add a framework (e.g., React)"
                  value={newFramework}
                  setValue={setNewFramework}
                  items={formData.frameworks}
                  setItems={(arr) =>
                    setFormData((p) => ({ ...p, frameworks: arr }))
                  }
                  badgeVariant="outline"
                  badgeClassName="
                    bg-purple-500/10 text-purple-700 border border-purple-500/20
                    dark:bg-purple-400/10 dark:text-purple-300 dark:border-purple-400/20
                  "
                />

                {/* Skills → Green */}
                <ChipInput
                  label="Skills"
                  placeholder="Add a skill (e.g., API Development)"
                  value={newSkill}
                  setValue={setNewSkill}
                  items={formData.skills}
                  setItems={(arr) => setFormData((p) => ({ ...p, skills: arr }))}
                  badgeVariant="secondary"
                  badgeClassName="
                    bg-emerald-500/10 text-emerald-700 border border-emerald-500/20
                    dark:bg-emerald-400/10 dark:text-emerald-300 dark:border-emerald-400/20
                  "
                />

                {/* Tools → Orange */}
                <ChipInput
                  label="Tools & Technologies"
                  placeholder="Add a tool (e.g., Docker, GitHub Actions)"
                  value={newTool}
                  setValue={setNewTool}
                  items={formData.toolsAndTechnologies}
                  setItems={(arr) =>
                    setFormData((p) => ({ ...p, toolsAndTechnologies: arr }))
                  }
                  badgeVariant="outline"
                  badgeClassName="
                    bg-orange-500/10 text-orange-700 border border-orange-500/20
                    dark:bg-orange-400/10 dark:text-orange-300 dark:border-orange-400/20
                  "
                />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t px-5 py-4 sm:px-6">
          <DialogFooter className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button
              variant="outline"
              onClick={onClose}
              className="w-full sm:w-auto"
              type="button"
            >
              Cancel
            </Button>
            <Button onClick={handleSave} className="w-full sm:w-auto" type="button">
              Save Changes
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default EditProjectModal;