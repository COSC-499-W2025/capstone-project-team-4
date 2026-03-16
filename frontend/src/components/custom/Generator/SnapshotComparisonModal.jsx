import React, { useState } from 'react';
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
} from 'lucide-react';
import { getAccessToken } from '@/lib/auth';

function getAuthHeaders() {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

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

const SetDeltaSection = ({ title, setDelta }) => {
  if (!setDelta) return null;
  const { added, removed } = setDelta;
  if (added.length === 0 && removed.length === 0) return null;

  return (
    <div className="space-y-1.5">
      <h4 className="text-sm font-medium text-gray-700">{title}</h4>
      {added.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {added.map((item, i) => (
            <Badge key={i} className="text-xs bg-green-50 text-green-700 border-green-200 gap-0.5">
              <Plus className="h-2.5 w-2.5" />{item}
            </Badge>
          ))}
        </div>
      )}
      {removed.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {removed.map((item, i) => (
            <Badge key={i} className="text-xs bg-red-50 text-red-600 border-red-200 gap-0.5">
              <Minus className="h-2.5 w-2.5" />{item}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
};

const SnapshotComparisonModal = ({ isOpen, onClose, project }) => {
  const [step, setStep] = useState('idle'); // idle | creating | comparing | done | error
  const [comparison, setComparison] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleLoad = async () => {
    if (!project?.projectId) return;
    setStep('creating');
    setErrorMsg(null);
    setComparison(null);

    try {
      await axios.post(
        `/api/snapshots/${project.projectId}/create`,
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
      // Reset state when closed
      setTimeout(() => {
        setStep('idle');
        setComparison(null);
        setErrorMsg(null);
      }, 300);
    }
  };

  const isLoading = step === 'creating' || step === 'comparing';

  const loadingMessage =
    step === 'creating' ? 'Creating snapshots...' : 'Comparing snapshots...';

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

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitCompare className="h-5 w-5 text-indigo-500" />
            Project Progress — {project?.name}
          </DialogTitle>
          <DialogDescription>
            Compare the midpoint state of the project to its current state
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto mt-4 space-y-5">
          {/* Idle — prompt to load */}
          {step === 'idle' && (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <GitCompare className="h-12 w-12 text-indigo-300" />
              <p className="text-gray-500 text-sm text-center max-w-xs">
                Generate a snapshot comparison to see how this project evolved from its midpoint to
                the current state.
              </p>
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
              {/* Commit range */}
              <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 font-mono flex items-center justify-between gap-2 flex-wrap">
                <span>Midpoint: {comparison.midpoint_commit_hash.slice(0, 8)}</span>
                <span className="text-gray-300">→</span>
                <span>Current: {comparison.current_commit_hash.slice(0, 8)}</span>
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

              {/* Count deltas */}
              <div>
                <h3 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-1.5">
                  <Layers className="h-4 w-4 text-gray-500" />
                  Counts
                </h3>
                <div className="bg-white border rounded-lg px-3 divide-y">
                  <MetricRow label="Languages" countDelta={comparison.counts?.language_count} />
                  <MetricRow label="Frameworks" countDelta={comparison.counts?.framework_count} />
                  <MetricRow label="Libraries" countDelta={comparison.counts?.library_count} />
                  <MetricRow label="Tools & Technologies" countDelta={comparison.counts?.tool_count} />
                  <MetricRow label="Skills" countDelta={comparison.counts?.skill_count} />
                </div>
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

              {/* Set changes */}
              {hasChanges ? (
                <div>
                  <h3 className="text-sm font-semibold text-gray-800 mb-3">Changes</h3>
                  <div className="space-y-3">
                    <SetDeltaSection title="Languages" setDelta={comparison.languages} />
                    <SetDeltaSection title="Frameworks" setDelta={comparison.frameworks} />
                    <SetDeltaSection title="Libraries" setDelta={comparison.libraries} />
                    <SetDeltaSection
                      title="Tools & Technologies"
                      setDelta={comparison.tools_and_technologies}
                    />
                    <SetDeltaSection title="Skills" setDelta={comparison.skills} />
                  </div>
                </div>
              ) : (
                <p className="text-center text-sm text-gray-400 py-2">
                  No added or removed items between midpoint and current
                </p>
              )}

              {/* Refresh button */}
              <div className="flex justify-end pt-1">
                <Button variant="outline" size="sm" onClick={handleLoad}>
                  Refresh
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SnapshotComparisonModal;
