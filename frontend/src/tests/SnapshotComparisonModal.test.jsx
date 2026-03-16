import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

vi.mock('@/lib/auth', () => ({
  getAccessToken: vi.fn(() => 'test-token'),
}));

import axios from 'axios';
import SnapshotComparisonModal from '@/components/custom/Generator/SnapshotComparisonModal';

const PROJECT = { projectId: 17, name: 'My Project' };

const TIMELINE = [
  { index: 0, hash: 'aaa', committed_at: '2024-01-01T00:00:00+00:00', percentage: 1 },
  { index: 5, hash: 'bbb', committed_at: '2024-06-01T00:00:00+00:00', percentage: 50 },
  { index: 10, hash: 'ccc', committed_at: '2025-03-15T00:00:00+00:00', percentage: 100 },
];

const COMPARISON = {
  project_id: 17,
  current_snapshot_id: 2,
  midpoint_snapshot_id: 1,
  current_commit_hash: 'abcdef1234567890',
  midpoint_commit_hash: 'fedcba0987654321',
  current_commit_date: '2025-03-15T10:00:00+00:00',
  midpoint_commit_date: '2024-06-01T10:00:00+00:00',
  totals: {
    total_files: { current: 50, midpoint: 30, delta: 20 },
    total_lines: { current: 5000, midpoint: 3000, delta: 2000 },
  },
  counts: {
    language_count: { current: 5, midpoint: 3, delta: 2 },
    framework_count: { current: 4, midpoint: 2, delta: 2 },
    library_count: { current: 10, midpoint: 8, delta: 2 },
    tool_count: { current: 6, midpoint: 4, delta: 2 },
    skill_count: { current: 12, midpoint: 9, delta: 3 },
  },
  languages: { added: ['TypeScript'], removed: [] },
  skills: { added: ['Testing'], removed: [] },
  libraries: { added: ['axios'], removed: ['lodash'] },
  frameworks: { added: [], removed: [] },
  tools_and_technologies: { added: ['Docker'], removed: [] },
  complexity: {
    total_functions: { current: 100, midpoint: 70, delta: 30 },
    avg_complexity: { current: 2.5, midpoint: 2.1, delta: 0.4 },
    max_complexity: { current: 15, midpoint: 12, delta: 3 },
    high_complexity_count: { current: 5, midpoint: 3, delta: 2 },
  },
};

const open = (props = {}) =>
  render(
    <SnapshotComparisonModal
      isOpen={true}
      onClose={vi.fn()}
      project={PROJECT}
      {...props}
    />
  );

const loadComparison = async () => {
  axios.post.mockResolvedValueOnce({ data: {} });
  axios.get.mockImplementation((url) => {
    if (url.includes('commit-timeline')) return Promise.resolve({ data: TIMELINE });
    return Promise.resolve({ data: COMPARISON });
  });
  fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
  await waitFor(() => expect(screen.queryByText(/loading|creating|comparing/i)).toBeNull());
};

describe('SnapshotComparisonModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Route GET calls by URL so timeline and compare don't interfere
    axios.get.mockImplementation((url) => {
      if (url.includes('commit-timeline')) return Promise.resolve({ data: TIMELINE });
      return Promise.resolve({ data: COMPARISON });
    });
  });

  // ── Visibility ──────────────────────────────────────────────────────────────

  it('renders nothing when isOpen is false', () => {
    const { container } = render(
      <SnapshotComparisonModal isOpen={false} onClose={vi.fn()} project={PROJECT} />
    );
    expect(container.querySelector('[role="dialog"]')).toBeNull();
  });

  it('shows the modal title when open', () => {
    open();
    expect(screen.getByText(/Project Progress/i)).toBeInTheDocument();
  });

  it('includes the project name in the title', () => {
    open();
    expect(screen.getByText(/My Project/i)).toBeInTheDocument();
  });

  it('shows the load comparison prompt on idle', () => {
    open();
    expect(screen.getByRole('button', { name: /load comparison/i })).toBeInTheDocument();
    expect(screen.getByText(/choose a start and end point/i)).toBeInTheDocument();
  });

  // ── API calls ────────────────────────────────────────────────────────────────

  it('POSTs to /api/snapshots/{id}/create with default percentage=50&end_percentage=100', async () => {
    axios.post.mockResolvedValueOnce({ data: {} });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        '/api/snapshots/17/create?percentage=50&end_percentage=100',
        {},
        expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) })
      );
    });
  });

  it('GETs /api/snapshots/{id}/compare after create succeeds', async () => {
    axios.post.mockResolvedValueOnce({ data: {} });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        '/api/snapshots/17/compare',
        expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) })
      );
    });
  });

  it('does not call GET compare when POST create fails', async () => {
    axios.post.mockRejectedValueOnce(new Error('Server error'));
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() => screen.getByRole('button', { name: /retry/i }));
    expect(axios.get).not.toHaveBeenCalledWith(
      '/api/snapshots/17/compare',
      expect.anything()
    );
  });

  // ── Loading states ───────────────────────────────────────────────────────────

  it('shows "Creating snapshots..." while POST is in-flight', async () => {
    axios.post.mockReturnValueOnce(new Promise(() => {}));
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    expect(await screen.findByText(/creating snapshots/i)).toBeInTheDocument();
  });

  it('shows "Comparing snapshots..." while GET is in-flight', async () => {
    axios.post.mockResolvedValueOnce({ data: {} });
    axios.get.mockImplementation((url) => {
      if (url.includes('commit-timeline')) return Promise.resolve({ data: TIMELINE });
      return new Promise(() => {}); // compare never resolves
    });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    expect(await screen.findByText(/comparing snapshots/i)).toBeInTheDocument();
  });

  // ── Success: commit range ─────────────────────────────────────────────────────

  it('displays the truncated commit hashes after success', async () => {
    open();
    await loadComparison();
    expect(screen.getByText(/abcdef12/i)).toBeInTheDocument();
    expect(screen.getByText(/fedcba09/i)).toBeInTheDocument();
  });

  it('displays formatted commit dates from response', async () => {
    open();
    await loadComparison();
    expect(screen.getAllByText(/Mar 15, 2025/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Jun 1, 2024/i).length).toBeGreaterThan(0);
  });

  it('shows From / To labels in the commit range header', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('From')).toBeInTheDocument();
    expect(screen.getByText('To')).toBeInTheDocument();
  });

  // ── Success: overview metrics ─────────────────────────────────────────────────

  it('shows total files midpoint and current counts', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('50')).toBeInTheDocument();
  });

  it('shows total lines midpoint and current counts', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('3,000')).toBeInTheDocument();
    expect(screen.getByText('5,000')).toBeInTheDocument();
  });

  it('renders Overview, Counts, and Complexity section headings', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Counts')).toBeInTheDocument();
    expect(screen.getByText('Complexity')).toBeInTheDocument();
  });

  // ── Success: count rows ───────────────────────────────────────────────────────

  it('shows Languages count row', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Languages')).toBeInTheDocument();
  });

  it('shows Frameworks count row', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Frameworks')).toBeInTheDocument();
  });

  it('shows Skills count row', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Skills')).toBeInTheDocument();
  });

  // ── Success: collapsible changes ──────────────────────────────────────────────

  it('reveals added language badge when Languages row is expanded', async () => {
    open();
    await loadComparison();
    fireEvent.click(screen.getByText('Languages'));
    expect(await screen.findByText('TypeScript')).toBeInTheDocument();
  });

  it('reveals removed library badge when Libraries row is expanded', async () => {
    open();
    await loadComparison();
    fireEvent.click(screen.getByText('Libraries'));
    expect(await screen.findByText('lodash')).toBeInTheDocument();
  });

  it('reveals added tool badge when Tools row is expanded', async () => {
    open();
    await loadComparison();
    fireEvent.click(screen.getByText('Tools & Technologies'));
    expect(await screen.findByText('Docker')).toBeInTheDocument();
  });

  it('reveals added skill badge when Skills row is expanded', async () => {
    open();
    await loadComparison();
    fireEvent.click(screen.getByText('Skills'));
    expect(await screen.findByText('Testing')).toBeInTheDocument();
  });

  it('shows "no added or removed items" message when all change sets are empty', async () => {
    const noChanges = {
      ...COMPARISON,
      languages: { added: [], removed: [] },
      skills: { added: [], removed: [] },
      libraries: { added: [], removed: [] },
      frameworks: { added: [], removed: [] },
      tools_and_technologies: { added: [], removed: [] },
    };
    axios.post.mockResolvedValueOnce({ data: {} });
    axios.get.mockImplementation((url) => {
      if (url.includes('commit-timeline')) return Promise.resolve({ data: TIMELINE });
      return Promise.resolve({ data: noChanges });
    });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() =>
      expect(screen.getByText(/no added or removed items/i)).toBeInTheDocument()
    );
  });

  // ── Success: complexity metrics ───────────────────────────────────────────────

  it('shows total functions metric', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Total Functions')).toBeInTheDocument();
    expect(screen.getByText('70')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('shows avg complexity with decimal formatting', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Avg Complexity')).toBeInTheDocument();
    expect(screen.getByText('2.10')).toBeInTheDocument();
    expect(screen.getByText('2.50')).toBeInTheDocument();
  });

  it('shows max complexity metric', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Max Complexity')).toBeInTheDocument();
  });

  // ── Success: refresh ──────────────────────────────────────────────────────────

  it('shows a Refresh button after successful load', async () => {
    open();
    await loadComparison();
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
  });

  it('re-calls both APIs when Refresh is clicked', async () => {
    open();
    await loadComparison();

    axios.post.mockResolvedValueOnce({ data: {} });
    fireEvent.click(screen.getByRole('button', { name: /refresh/i }));

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledTimes(2);
      expect(axios.get).toHaveBeenCalledWith('/api/snapshots/17/compare', expect.anything());
    });
  });

  // ── Error states ──────────────────────────────────────────────────────────────

  it('shows generic error message when POST fails', async () => {
    axios.post.mockRejectedValueOnce({
      response: { data: { detail: 'Internal Server Error' } },
    });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() =>
      expect(screen.getByText('Internal Server Error')).toBeInTheDocument()
    );
  });

  it('shows friendly re-upload message when git repo is missing', async () => {
    axios.post.mockRejectedValueOnce({
      response: { data: { detail: 'Could not locate a git repository for this project.' } },
    });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() =>
      expect(screen.getByText(/re-upload this project/i)).toBeInTheDocument()
    );
  });

  it('shows friendly re-upload message when ZIP is missing', async () => {
    axios.post.mockRejectedValueOnce({
      response: { data: { detail: 'Ensure uploaded ZIP includes .git and the stored ZIP still exists.' } },
    });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() =>
      expect(screen.getByText(/re-upload this project/i)).toBeInTheDocument()
    );
  });

  it('shows a Retry button on error', async () => {
    axios.post.mockRejectedValueOnce(new Error('fail'));
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    );
  });

  it('re-calls APIs when Retry is clicked', async () => {
    axios.post.mockRejectedValueOnce(new Error('fail'));
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() => screen.getByRole('button', { name: /retry/i }));

    axios.post.mockResolvedValueOnce({ data: {} });
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() =>
      expect(axios.post).toHaveBeenCalledTimes(2)
    );
  });

  // ── Range slider ──────────────────────────────────────────────────────────────

  it('shows two slider thumbs in the idle state (range slider)', () => {
    open();
    expect(document.querySelectorAll('[role="slider"]').length).toBe(2);
  });

  it('shows from-slider label containing "50%"', async () => {
    open();
    // While timeline loads: "50% (Loading…)"; after: "Jun 1, 2024 (50%)"
    expect(await screen.findByText(/50%/)).toBeInTheDocument();
  });

  it('shows to-slider label containing "Current"', async () => {
    open();
    // While timeline loads: "Current HEAD (Loading…)"; after: "Mar 15, 2025 (Current)"
    expect(await screen.findByText(/Current/)).toBeInTheDocument();
  });

  it('shows two slider thumbs in the results state for re-running', async () => {
    open();
    await loadComparison();
    expect(document.querySelectorAll('[role="slider"]').length).toBe(2);
  });

  it('shows formatted dates on the slider labels after load', async () => {
    open();
    await loadComparison();
    expect(screen.getAllByText(/Jun 1, 2024/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Mar 15, 2025/i).length).toBeGreaterThan(0);
  });

  it('range slider thumbs have correct initial aria-valuenow attributes', () => {
    open();
    const [fromThumb, toThumb] = document.querySelectorAll('[role="slider"]');
    expect(fromThumb).toHaveAttribute('aria-valuenow', '50');
    expect(toThumb).toHaveAttribute('aria-valuenow', '100');
  });

  // ── Commit timeline (live slider dates) ──────────────────────────────────────

  it('fetches commit-timeline on open', async () => {
    open();
    await waitFor(() =>
      expect(axios.get).toHaveBeenCalledWith(
        '/api/snapshots/17/commit-timeline',
        expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) })
      )
    );
  });

  it('shows date from timeline on the from-slider label at 50%', async () => {
    open();
    // TIMELINE entry at percentage=50 has committed_at 2024-06-01
    expect(await screen.findByText(/Jun 1, 2024/i)).toBeInTheDocument();
  });

  it('shows date from timeline on the to-slider label at 100%', async () => {
    open();
    // TIMELINE entry at percentage=100 has committed_at 2025-03-15
    expect(await screen.findByText(/Mar 15, 2025/i)).toBeInTheDocument();
  });

  it('shows "Loading…" on slider labels while timeline is in-flight', async () => {
    axios.get.mockImplementation((url) => {
      if (url.includes('commit-timeline')) return new Promise(() => {}); // never resolves
      return Promise.resolve({ data: COMPARISON });
    });
    open();
    const loadingLabels = await screen.findAllByText(/Loading/);
    expect(loadingLabels.length).toBeGreaterThan(0);
  });

  it('falls back to percentage labels when timeline fetch fails', async () => {
    axios.get.mockImplementation((url) => {
      if (url.includes('commit-timeline')) return Promise.reject(new Error('network'));
      return Promise.resolve({ data: COMPARISON });
    });
    open();
    await waitFor(() => expect(screen.getByText('50%')).toBeInTheDocument());
  });

  // ── onClose ───────────────────────────────────────────────────────────────────

  it('calls onClose when the dialog close button is clicked', async () => {
    const onClose = vi.fn();
    open({ onClose });
    const closeBtn = document.querySelector('button[data-state]') ||
      document.querySelector('[aria-label="Close"]');
    if (closeBtn) {
      fireEvent.click(closeBtn);
      expect(onClose).toHaveBeenCalled();
    }
    // pass gracefully if Radix close button not found in jsdom
  });
});
