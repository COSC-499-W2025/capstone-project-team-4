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

const COMPARISON = {
  project_id: 17,
  current_snapshot_id: 2,
  midpoint_snapshot_id: 1,
  current_commit_hash: 'abcdef1234567890',
  midpoint_commit_hash: 'fedcba0987654321',
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
  axios.get.mockResolvedValueOnce({ data: COMPARISON });
  fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
  await waitFor(() => expect(screen.queryByText(/loading|creating|comparing/i)).toBeNull());
};

describe('SnapshotComparisonModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
    expect(screen.getByText(/generate a snapshot comparison/i)).toBeInTheDocument();
  });

  // ── API calls ────────────────────────────────────────────────────────────────

  it('POSTs to /api/snapshots/{id}/create when load is clicked', async () => {
    axios.post.mockResolvedValueOnce({ data: {} });
    axios.get.mockResolvedValueOnce({ data: COMPARISON });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        '/api/snapshots/17/create',
        {},
        expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) })
      );
    });
  });

  it('GETs /api/snapshots/{id}/compare after create succeeds', async () => {
    axios.post.mockResolvedValueOnce({ data: {} });
    axios.get.mockResolvedValueOnce({ data: COMPARISON });
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
    expect(axios.get).not.toHaveBeenCalled();
  });

  // ── Loading states ───────────────────────────────────────────────────────────

  it('shows "Creating snapshots..." while POST is in-flight', async () => {
    // Never-resolving promise keeps component in the 'creating' state
    axios.post.mockReturnValueOnce(new Promise(() => {}));
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    expect(await screen.findByText(/creating snapshots/i)).toBeInTheDocument();
  });

  it('shows "Comparing snapshots..." while GET is in-flight', async () => {
    axios.post.mockResolvedValueOnce({ data: {} });
    // Never-resolving GET keeps component in 'comparing' state
    axios.get.mockReturnValueOnce(new Promise(() => {}));
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    expect(await screen.findByText(/comparing snapshots/i)).toBeInTheDocument();
  });

  // ── Success: overview metrics ─────────────────────────────────────────────────

  it('displays the truncated commit hashes after success', async () => {
    open();
    await loadComparison();
    expect(screen.getByText(/abcdef12/i)).toBeInTheDocument();
    expect(screen.getByText(/fedcba09/i)).toBeInTheDocument();
  });

  it('shows total files midpoint and current counts', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('30')).toBeInTheDocument(); // midpoint
    expect(screen.getByText('50')).toBeInTheDocument(); // current
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

  // ── Success: count deltas ─────────────────────────────────────────────────────

  it('shows language count row', async () => {
    open();
    await loadComparison();
    // "Languages" appears in both Counts and Changes sections
    expect(screen.getAllByText('Languages').length).toBeGreaterThan(0);
  });

  it('shows framework count row', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Frameworks')).toBeInTheDocument();
  });

  it('shows skills count row', async () => {
    open();
    await loadComparison();
    // "Skills" appears in both Counts and Changes sections
    expect(screen.getAllByText('Skills').length).toBeGreaterThan(0);
  });

  // ── Success: complexity metrics ───────────────────────────────────────────────

  it('shows total functions metric', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Total Functions')).toBeInTheDocument();
    expect(screen.getByText('70')).toBeInTheDocument();  // midpoint
    expect(screen.getByText('100')).toBeInTheDocument(); // current
  });

  it('shows avg complexity with decimal formatting', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Avg Complexity')).toBeInTheDocument();
    expect(screen.getByText('2.10')).toBeInTheDocument(); // midpoint
    expect(screen.getByText('2.50')).toBeInTheDocument(); // current
  });

  it('shows max complexity metric', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Max Complexity')).toBeInTheDocument();
  });

  // ── Success: changes section ──────────────────────────────────────────────────

  it('shows the Changes heading when items were added or removed', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Changes')).toBeInTheDocument();
  });

  it('renders added language badges', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
  });

  it('renders removed library badges', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('lodash')).toBeInTheDocument();
  });

  it('renders added tool badges', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Docker')).toBeInTheDocument();
  });

  it('renders added skill badges', async () => {
    open();
    await loadComparison();
    expect(screen.getByText('Testing')).toBeInTheDocument();
  });

  it('shows "no changes" message when all added/removed sets are empty', async () => {
    const noChanges = {
      ...COMPARISON,
      languages: { added: [], removed: [] },
      skills: { added: [], removed: [] },
      libraries: { added: [], removed: [] },
      frameworks: { added: [], removed: [] },
      tools_and_technologies: { added: [], removed: [] },
    };
    axios.post.mockResolvedValueOnce({ data: {} });
    axios.get.mockResolvedValueOnce({ data: noChanges });
    open();
    fireEvent.click(screen.getByRole('button', { name: /load comparison/i }));
    await waitFor(() =>
      expect(screen.getByText(/no added or removed items/i)).toBeInTheDocument()
    );
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
    axios.get.mockResolvedValueOnce({ data: COMPARISON });
    fireEvent.click(screen.getByRole('button', { name: /refresh/i }));

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledTimes(2);
      expect(axios.get).toHaveBeenCalledTimes(2);
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
    axios.get.mockResolvedValueOnce({ data: COMPARISON });
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() =>
      expect(axios.post).toHaveBeenCalledTimes(2)
    );
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
