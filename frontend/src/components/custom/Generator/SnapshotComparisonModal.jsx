import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import {
  GitCompare,
  Loader2,
  Plus,
  Minus,
  TrendingUp,
  TrendingDown,
  Minus as MinusFlat,
  FileText,
  Code,
  Layers,
  ChevronDown,
} from 'lucide-react';
import { getAccessToken } from '@/lib/auth';

function getAuthHeaders() {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const formatCommitDate = (isoString) => {
  if (!isoString) return null;
  return new Date(isoString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  });
};

/** Find the closest timeline entry to the given percentage. */
const getDateAtPct = (pct, timeline) => {
  if (!Array.isArray(timeline) || timeline.length === 0) return null;
  const closest = timeline.reduce((prev, curr) =>
    Math.abs(curr.percentage - pct) < Math.abs(prev.percentage - pct) ? curr : prev
  );
  return closest.committed_at ?? null;
};

const DeltaBadge = ({ delta, formatFn }) => {
  const display = formatFn ? formatFn(delta) : delta;
  if (delta > 0) {
    return (
      <span className="inline-flex items-center gap-0.5 text-green-600 font-semibold text-xs">
        <TrendingUp className="h-3 w-3" />+{display}
      </span>
    );
  }
  if (delta < 0) {
    return (
      <span className="inline-flex items-center gap-0.5 text-red-500 font-semibold text-xs">
        <TrendingDown className="h-3 w-3" />{display}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-0.5 text-gray-400 font-semibold text-xs">
      <MinusFlat className="h-3 w-3" />0
    </span>
  );
};

/** Count row that expands to show added/removed badges for that category. */
const CollapsibleMetricRow = ({ label, countDelta, setDelta }) => {
  const [expanded, setExpanded] = useState(false);
  if (!countDelta) return null;

  const hasChanges =
    setDelta && (setDelta.added.length > 0 || setDelta.removed.length > 0);

  return (
    <div className="border-b last:border-0">
      <div
        className={`flex items-center justify-between py-1.5 ${hasChanges ? 'cursor-pointer hover:bg-gray-50 rounded' : ''}`}
        onClick={() => hasChanges && setExpanded((e) => !e)}
      >
        <div className="flex items-center gap-1 text-sm text-gray-600">
          {hasChanges ? (
            <ChevronDown
              className={`h-3 w-3 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            />
          ) : (
            <span className="inline-block w-3" />
          )}
          {label}
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-gray-400 text-xs">{countDelta.midpoint.toLocaleString()}</span>
          <span className="text-gray-300">→</span>
          <span className="font-medium">{countDelta.current.toLocaleString()}</span>
          <DeltaBadge delta={countDelta.delta} />
        </div>
      </div>

      {expanded && hasChanges && (
        <div className="pb-2 pl-5 space-y-1.5">
          {setDelta.added.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {setDelta.added.map((item, i) => (
                <Badge key={i} className="text-xs bg-green-50 text-green-700 border-green-200 gap-0.5">
                  <Plus className="h-2.5 w-2.5" />{item}
                </Badge>
              ))}
            </div>
          )}
          {setDelta.removed.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {setDelta.removed.map((item, i) => (
                <Badge key={i} className="text-xs bg-red-50 text-red-600 border-red-200 gap-0.5">
                  <Minus className="h-2.5 w-2.5" />{item}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const MetricRow = ({ label, countDelta }) => {
  if (!countDelta) return null;
  return (
    <div className="flex items-center justify-between py-1.5 border-b last:border-0">
      <span className="text-sm text-gray-600">{label}</span>
      <div className="flex items-center gap-3 text-sm">
        <span className="text-gray-400 text-xs">{countDelta.midpoint.toLocaleString()}</span>
        <span className="text-gray-300">→</span>
        <span className="font-medium">{countDelta.current.toLocaleString()}</span>
        <DeltaBadge delta={countDelta.delta} />
      </div>
    </div>
  );
};

/** Range slider showing two labeled date/percentage points. */
const RangeSliderControl = ({ fromPct, toPct, onChange, commitTimeline, timelineLoading }) => {
  const fromDateStr = getDateAtPct(fromPct, commitTimeline);
  const toDateStr = getDateAtPct(toPct, commitTimeline);

  const fromLabel = timelineLoading
    ? `${fromPct}% (Loading…)`
    : fromDateStr
    ? `${formatCommitDate(fromDateStr)} (${fromPct}%)`
    : `${fromPct}%`;

  const toLabel = timelineLoading
    ? toPct >= 100 ? 'Latest HEAD (Loading…)' : `${toPct}% (Loading…)`
    : toPct >= 100
    ? (toDateStr ? `${formatCommitDate(toDateStr)} (Latest)` : 'Latest HEAD')
    : toDateStr
    ? `${formatCommitDate(toDateStr)} (${toPct}%)`
    : `${toPct}%`;

  return (
    <div className="w-full max-w-sm space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-indigo-600 font-semibold">{fromLabel}</span>
        <span className="text-indigo-600 font-semibold">{toLabel}</span>
      </div>
      <Slider
        min={1}
        max={100}
        step={1}
        value={[fromPct, toPct]}
        onValueChange={([from, to]) => onChange(from, to)}
        minStepsBetweenThumbs={1}
      />
      <div className="flex justify-between text-xs text-gray-400">
        <span>Earliest</span>
        <span>Latest</span>
      </div>
    </div>
  );
};

const SnapshotComparisonModal = ({ isOpen, onClose, project }) => {
  const [step, setStep] = useState('idle');
  const [comparison, setComparison] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [fromPct, setFromPct] = useState(50);
  const [toPct, setToPct] = useState(100);
  const [commitTimeline, setCommitTimeline] = useState(null);
  const timelineLoading = isOpen && !!project?.projectId && !Array.isArray(commitTimeline);

  useEffect(() => {
    if (!isOpen || !project?.projectId) return;
    axios
      .get(`/api/snapshots/${project.projectId}/commit-timeline`, { headers: getAuthHeaders() })
      .then((res) => setCommitTimeline(res.data))
      .catch(() => setCommitTimeline([]));
  }, [isOpen, project?.projectId]);

  const handleLoad = async () => {
    if (!project?.projectId) return;
    setStep('creating');
    setErrorMsg(null);
    setComparison(null);

    try {
      await axios.post(
        `/api/snapshots/${project.projectId}/create?percentage=${fromPct}&end_percentage=${toPct}`,
        {},
        { headers: getAuthHeaders() }
      );

      setStep('comparing');

      const res = await axios.get(
        `/api/snapshots/${project.projectId}/compare`,
        { headers: getAuthHeaders() }
      );

      setComparison(res.data);
      setStep('done');
    } catch (err) {
      console.error('Snapshot comparison error:', err);
      const detail = err.response?.data?.detail || err.message || 'Failed to load snapshot comparison';
      const isGitMissing = detail.includes('git repository') || detail.includes('ZIP');
      setErrorMsg(
        isGitMissing
          ? 'The original project ZIP is no longer available. Re-upload this project to enable snapshot comparisons.'
          : detail
      );
      setStep('error');
    }
  };

  const handleOpenChange = (open) => {
    if (!open) {
      onClose();
      setTimeout(() => {
        setStep('idle');
        setComparison(null);
        setErrorMsg(null);
        setFromPct(50);
        setToPct(100);
        setCommitTimeline(null);
      }, 300);
    }
  };

  const isLoading = step === 'creating' || step === 'comparing';

  const hasChanges =
    comparison &&
    (comparison.languages.added.length > 0 ||
      comparison.languages.removed.length > 0 ||
      comparison.frameworks.added.length > 0 ||
      comparison.frameworks.removed.length > 0 ||
      comparison.libraries.added.length > 0 ||
      comparison.libraries.removed.length > 0 ||
      comparison.tools_and_technologies.added.length > 0 ||
      comparison.tools_and_technologies.removed.length > 0 ||
      comparison.skills.added.length > 0 ||
      comparison.skills.removed.length > 0);

  const loadingMessage =
    step === 'creating' ? 'Creating snapshots...' : 'Comparing snapshots...';

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitCompare className="h-5 w-5 text-indigo-500" />
            Project Progress — {project?.name}
          </DialogTitle>
          <DialogDescription>
            Drag both handles to compare any two points in the commit history
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto mt-4 space-y-5">
          {/* Idle — prompt to load */}
          {step === 'idle' && (
            <div className="flex flex-col items-center justify-center py-10 gap-5">
              <GitCompare className="h-12 w-12 text-indigo-300" />
              <p className="text-gray-500 text-sm text-center max-w-xs">
                Choose a start and end point in the commit history to compare.
              </p>
              <RangeSliderControl
                fromPct={fromPct}
                toPct={toPct}
                onChange={(from, to) => { setFromPct(from); setToPct(to); }}
                commitTimeline={commitTimeline}
                timelineLoading={timelineLoading}
              />
              <Button onClick={handleLoad} className="bg-indigo-600 hover:bg-indigo-700 text-white">
                Load Comparison
              </Button>
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
              <span className="text-gray-600 text-sm">{loadingMessage}</span>
            </div>
          )}

          {/* Error */}
          {step === 'error' && (
            <div className="flex flex-col items-center justify-center py-10 gap-3">
              <p className="text-red-500 text-sm font-medium">Failed to load comparison</p>
              <p className="text-gray-400 text-xs text-center max-w-sm">{errorMsg}</p>
              <Button variant="outline" size="sm" onClick={handleLoad}>
                Retry
              </Button>
            </div>
          )}

          {/* Results */}
          {step === 'done' && comparison && (
            <>
              {/* Commit range — shows dates */}
              <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 flex items-center justify-between gap-2 flex-wrap">
                <div className="flex flex-col">
                  <span className="text-gray-400">From</span>
                  <span className="font-medium text-gray-700">
                    {comparison.midpoint_commit_date
                      ? formatCommitDate(comparison.midpoint_commit_date)
                      : comparison.midpoint_commit_hash.slice(0, 8)}
                  </span>
                  <span className="font-mono text-gray-400">{comparison.midpoint_commit_hash.slice(0, 8)}</span>
                </div>
                <span className="text-gray-300 text-base">→</span>
                <div className="flex flex-col items-end">
                  <span className="text-gray-400">To</span>
                  <span className="font-medium text-gray-700">
                    {comparison.current_commit_date
                      ? formatCommitDate(comparison.current_commit_date)
                      : comparison.current_commit_hash.slice(0, 8)}
                  </span>
                  <span className="font-mono text-gray-400">{comparison.current_commit_hash.slice(0, 8)}</span>
                </div>
              </div>

              {/* Totals */}
              <div>
                <h3 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-gray-500" />
                  Overview
                </h3>
                <div className="bg-white border rounded-lg px-3 divide-y">
                  <MetricRow label="Total Files" countDelta={comparison.totals?.total_files} />
                  <MetricRow label="Total Lines of Code" countDelta={comparison.totals?.total_lines} />
                </div>
              </div>

              {/* Counts + Changes merged as collapsible rows */}
              <div>
                <h3 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-1.5">
                  <Layers className="h-4 w-4 text-gray-500" />
                  Counts
                  <span className="text-xs font-normal text-gray-400 ml-1">(click rows with changes to expand)</span>
                </h3>
                <div className="bg-white border rounded-lg px-3 divide-y">
                  <CollapsibleMetricRow
                    label="Languages"
                    countDelta={comparison.counts?.language_count}
                    setDelta={comparison.languages}
                  />
                  <CollapsibleMetricRow
                    label="Frameworks"
                    countDelta={comparison.counts?.framework_count}
                    setDelta={comparison.frameworks}
                  />
                  <CollapsibleMetricRow
                    label="Libraries"
                    countDelta={comparison.counts?.library_count}
                    setDelta={comparison.libraries}
                  />
                  <CollapsibleMetricRow
                    label="Tools & Technologies"
                    countDelta={comparison.counts?.tool_count}
                    setDelta={comparison.tools_and_technologies}
                  />
                  <CollapsibleMetricRow
                    label="Skills"
                    countDelta={comparison.counts?.skill_count}
                    setDelta={comparison.skills}
                  />
                </div>
                {!hasChanges && (
                  <p className="text-center text-sm text-gray-400 py-2">
                    No added or removed items between the two points
                  </p>
                )}
              </div>

              {/* Complexity */}
              {comparison.complexity && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-1.5">
                    <Code className="h-4 w-4 text-gray-500" />
                    Complexity
                  </h3>
                  <div className="bg-white border rounded-lg px-3 divide-y">
                    <MetricRow
                      label="Total Functions"
                      countDelta={comparison.complexity.total_functions}
                    />
                    <MetricRow
                      label="Max Complexity"
                      countDelta={comparison.complexity.max_complexity}
                    />
                    <MetricRow
                      label="High Complexity Functions"
                      countDelta={comparison.complexity.high_complexity_count}
                    />
                    {comparison.complexity.avg_complexity && (
                      <div className="flex items-center justify-between py-1.5">
                        <span className="text-sm text-gray-600">Avg Complexity</span>
                        <div className="flex items-center gap-3 text-sm">
                          <span className="text-gray-400 text-xs">
                            {comparison.complexity.avg_complexity.midpoint?.toFixed(2)}
                          </span>
                          <span className="text-gray-300">→</span>
                          <span className="font-medium">
                            {comparison.complexity.avg_complexity.current?.toFixed(2)}
                          </span>
                          <DeltaBadge
                            delta={comparison.complexity.avg_complexity.delta}
                            formatFn={(d) => Math.abs(d).toFixed(2)}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Re-run with different range */}
              <div className="pt-2 border-t space-y-3">
                <p className="text-xs text-gray-500">Adjust range and reload to compare a different period</p>
                <div className="flex justify-center">
                  <RangeSliderControl
                    fromPct={fromPct}
                    toPct={toPct}
                    onChange={(from, to) => { setFromPct(from); setToPct(to); }}
                    commitTimeline={commitTimeline}
                    timelineLoading={timelineLoading}
                  />
                </div>
                <div className="flex justify-end pt-1">
                  <Button variant="outline" size="sm" onClick={handleLoad}>
                    Refresh
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SnapshotComparisonModal;
