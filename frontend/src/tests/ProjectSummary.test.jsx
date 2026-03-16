import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('axios', () => ({
  default: { get: vi.fn() },
}));

vi.mock('@/components/custom/Generator/EditProjectModal', () => ({
  default: ({ isOpen, onClose, onSave, project }) =>
    isOpen ? (
      <div data-testid="edit-modal">
        <button onClick={onClose}>Close</button>
        <button onClick={() => onSave({ ...project, name: 'Edited Name' })}>Save</button>
      </div>
    ) : null,
}));

vi.mock('@/components/custom/Generator/SnapshotComparisonModal', () => ({
  default: ({ isOpen, onClose, project }) =>
    isOpen ? (
      <div data-testid="snapshot-modal">
        <span data-testid="snapshot-project-name">{project?.name}</span>
        <button onClick={onClose}>Close Snapshot</button>
      </div>
    ) : null,
}));

vi.mock('@/lib/auth', () => ({
  getAccessToken: vi.fn(() => 'test-token'),
}));

import axios from 'axios';
import ProjectSummary from '@/components/custom/Generator/ProjectSummary';

const makeProject = (overrides = {}) => ({
  projectId: 1,
  name: 'Test Project',
  contributions: 42,
  contributorCount: 3,
  date: '2026-03-08T00:00:00Z',
  projectStartedAt: '2025-01-01T00:00:00Z',
  totalLinesOfCode: 1500,
  languages: ['JavaScript', 'Python'],
  frameworks: ['React'],
  skills: ['Frontend'],
  toolsAndTechnologies: ['Docker'],
  description: 'A test project',
  complexity: {
    total_functions: 10,
    avg_complexity: 2.5,
    max_complexity: 8,
    high_complexity_count: 1,
  },
  ...overrides,
});

describe('ProjectSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when projects is null', () => {
    const { container } = render(<ProjectSummary projects={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when projects is empty', () => {
    const { container } = render(<ProjectSummary projects={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the project name', () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    expect(screen.getByText('Test Project')).toBeInTheDocument();
  });

  it('displays files analyzed count', () => {
    render(<ProjectSummary projects={[makeProject({ contributions: 99 })]} />);
    expect(screen.getByText('99')).toBeInTheDocument();
  });

  it('displays contributor count', () => {
    render(<ProjectSummary projects={[makeProject({ contributorCount: 5 })]} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('shows total lines of code when > 0', () => {
    render(<ProjectSummary projects={[makeProject({ totalLinesOfCode: 1500 })]} />);
    expect(screen.getByText('1,500')).toBeInTheDocument();
  });

  it('hides lines of code section when totalLinesOfCode is 0', () => {
    render(<ProjectSummary projects={[makeProject({ totalLinesOfCode: 0 })]} />);
    expect(screen.queryByText('Total Lines of Code')).not.toBeInTheDocument();
  });

  it('hides lines of code section when totalLinesOfCode is missing', () => {
    render(<ProjectSummary projects={[makeProject({ totalLinesOfCode: undefined })]} />);
    expect(screen.queryByText('Total Lines of Code')).not.toBeInTheDocument();
  });

  it('renders language badges', () => {
    render(<ProjectSummary projects={[makeProject({ languages: ['Java', 'XML'] })]} />);
    expect(screen.getByText('Java')).toBeInTheDocument();
    expect(screen.getByText('XML')).toBeInTheDocument();
  });

  it('hides languages section when languages array is empty', () => {
    render(<ProjectSummary projects={[makeProject({ languages: [] })]} />);
    expect(screen.queryByText('Languages:')).not.toBeInTheDocument();
  });

  it('renders complexity metrics', () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    expect(screen.getByText('Total Functions:')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('Avg Complexity:')).toBeInTheDocument();
    expect(screen.getByText('2.50')).toBeInTheDocument();
    expect(screen.getByText('Max Complexity:')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
  });

  it('shows high complexity count when > 0', () => {
    render(<ProjectSummary projects={[makeProject({ complexity: { high_complexity_count: 7, total_functions: 10, avg_complexity: 2, max_complexity: 5 } })]} />);
    expect(screen.getByText('High Complexity Functions:')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
  });

  it('hides high complexity count when 0', () => {
    render(<ProjectSummary projects={[makeProject({ complexity: { high_complexity_count: 0, total_functions: 5, avg_complexity: 1, max_complexity: 2 } })]} />);
    expect(screen.queryByText('High Complexity Functions:')).not.toBeInTheDocument();
  });

  it('hides complexity section when complexity is empty', () => {
    render(<ProjectSummary projects={[makeProject({ complexity: {} })]} />);
    expect(screen.queryByText('Complexity Metrics:')).not.toBeInTheDocument();
  });

  it('shows N/A for missing dates', () => {
    render(<ProjectSummary projects={[makeProject({ date: null, projectStartedAt: null })]} />);
    const naElements = screen.getAllByText('N/A');
    expect(naElements.length).toBeGreaterThanOrEqual(2);
  });

  it('renders the description', () => {
    render(<ProjectSummary projects={[makeProject({ description: 'A cool project' })]} />);
    expect(screen.getByText('A cool project')).toBeInTheDocument();
  });

  it('hides description when not provided', () => {
    render(<ProjectSummary projects={[makeProject({ description: null })]} />);
    expect(screen.queryByText('Description:')).not.toBeInTheDocument();
  });

  it('renders frameworks and tools badges', () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('Docker')).toBeInTheDocument();
  });

  it('shows +N more badge when languages exceed 8', () => {
    const manyLanguages = ['A','B','C','D','E','F','G','H','I','J'];
    render(<ProjectSummary projects={[makeProject({ languages: manyLanguages })]} />);
    expect(screen.getByText('+2 more')).toBeInTheDocument();
  });

  it('expands language list when clicking +N more', () => {
    const manyLanguages = ['A','B','C','D','E','F','G','H','I','J'];
    render(<ProjectSummary projects={[makeProject({ languages: manyLanguages })]} />);
    fireEvent.click(screen.getByText('+2 more'));
    expect(screen.getByText('I')).toBeInTheDocument();
    expect(screen.getByText('J')).toBeInTheDocument();
  });

  it('sorts by date by default (newest first)', () => {
    const projects = [
      makeProject({ projectId: 1, name: 'Older', date: '2025-01-01T00:00:00Z' }),
      makeProject({ projectId: 2, name: 'Newer', date: '2026-01-01T00:00:00Z' }),
    ];
    render(<ProjectSummary projects={projects} />);
    const cards = screen.getAllByText(/Older|Newer/);
    expect(cards[0].textContent).toBe('Newer');
    expect(cards[1].textContent).toBe('Older');
  });

  it('renders multiple project cards', () => {
    const projects = [
      makeProject({ projectId: 1, name: 'Project Alpha' }),
      makeProject({ projectId: 2, name: 'Project Beta' }),
    ];
    render(<ProjectSummary projects={projects} />);
    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
    expect(screen.getByText('Project Beta')).toBeInTheDocument();
  });

  it('opens edit modal when edit button is clicked', () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    // Edit button has no title; GitCompare button has title="View project progress"
    const editButton = screen.getAllByRole('button')
      .filter(b => b.querySelector('svg') && !b.title)[0];
    fireEvent.click(editButton);
    expect(screen.getByTestId('edit-modal')).toBeInTheDocument();
  });

  it('closes edit modal when onClose is called', () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    const editButton = screen.getAllByRole('button')
      .filter(b => b.querySelector('svg') && !b.title)[0];
    fireEvent.click(editButton);
    expect(screen.getByTestId('edit-modal')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Close'));
    expect(screen.queryByTestId('edit-modal')).not.toBeInTheDocument();
  });

  it('calls onUpdateProject with updated data when saving', () => {
    const onUpdateProject = vi.fn();
    render(<ProjectSummary projects={[makeProject()]} onUpdateProject={onUpdateProject} />);
    const editButton = screen.getAllByRole('button')
      .filter(b => b.querySelector('svg') && !b.title)[0];
    fireEvent.click(editButton);
    fireEvent.click(screen.getByText('Save'));
    expect(onUpdateProject).toHaveBeenCalledWith(0, expect.objectContaining({ name: 'Edited Name' }));
  });

  it('opens contributor modal when contributor count is clicked', async () => {
    axios.get.mockResolvedValue({
      data: {
        total_contributors: 2,
        items: [
          { author: 'Alice <alice@example.com>', total_lines_added: 100, total_lines_deleted: 20, total_lines_changed: 120 },
        ],
      },
    });

    render(<ProjectSummary projects={[makeProject({ projectId: 5, contributorCount: 2 })]} />);
    fireEvent.click(screen.getByText('2'));

    await waitFor(() => {
      expect(screen.getByText('Total Contributors:')).toBeInTheDocument();
    });
    expect(axios.get).toHaveBeenCalledWith('/api/projects/5/contributors/default-branch-stats');
  });

  it('does not crash when top contributor has zero total_lines_changed', async () => {
    axios.get.mockResolvedValue({
      data: {
        total_contributors: 1,
        items: [
          { author: 'Alice <alice@example.com>', total_lines_added: 0, total_lines_deleted: 0, total_lines_changed: 0 },
        ],
      },
    });

    render(<ProjectSummary projects={[makeProject({ projectId: 5, contributorCount: 17 })]} />);
    fireEvent.click(screen.getByText('17'));

    await waitFor(() => {
      expect(screen.getByText('Total Contributors:')).toBeInTheDocument();
    });
    // progress bar div should not be rendered (guarded by total_lines_changed > 0)
    expect(document.querySelector('.bg-blue-500.rounded-full')).toBeNull();
  });

  it('shows error message when contributor fetch fails', async () => {
    axios.get.mockRejectedValue({ message: 'Network Error' });

    render(<ProjectSummary projects={[makeProject({ projectId: 5, contributorCount: 2 })]} />);
    fireEvent.click(screen.getByText('2'));

    await waitFor(() => {
      expect(screen.getByText('Failed to load contributors')).toBeInTheDocument();
    });
  });

  // ── Snapshot comparison button ───────────────────────────────────────────────

  it('shows the GitCompare button for projects with a projectId', () => {
    render(<ProjectSummary projects={[makeProject({ projectId: 42 })]} />);
    expect(screen.getByTitle('View project progress')).toBeInTheDocument();
  });

  it('does not show the GitCompare button when projectId is missing', () => {
    render(<ProjectSummary projects={[makeProject({ projectId: undefined })]} />);
    expect(screen.queryByTitle('View project progress')).not.toBeInTheDocument();
  });

  it('opens the snapshot comparison modal when GitCompare is clicked', () => {
    render(<ProjectSummary projects={[makeProject({ projectId: 7, name: 'Snap Project' })]} />);
    fireEvent.click(screen.getByTitle('View project progress'));
    expect(screen.getByTestId('snapshot-modal')).toBeInTheDocument();
  });

  it('passes the correct project to the snapshot modal', () => {
    render(<ProjectSummary projects={[makeProject({ projectId: 7, name: 'Snap Project' })]} />);
    fireEvent.click(screen.getByTitle('View project progress'));
    expect(screen.getByTestId('snapshot-project-name').textContent).toBe('Snap Project');
  });

  it('closes the snapshot modal when onClose is called', () => {
    render(<ProjectSummary projects={[makeProject({ projectId: 7 })]} />);
    fireEvent.click(screen.getByTitle('View project progress'));
    expect(screen.getByTestId('snapshot-modal')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Close Snapshot'));
    expect(screen.queryByTestId('snapshot-modal')).not.toBeInTheDocument();
  });

  it('shows GitCompare button for each project that has a projectId', () => {
    const projects = [
      makeProject({ projectId: 1, name: 'Alpha' }),
      makeProject({ projectId: 2, name: 'Beta' }),
    ];
    render(<ProjectSummary projects={projects} />);
    expect(screen.getAllByTitle('View project progress')).toHaveLength(2);
  });

  it('snapshot modal only opens for the clicked project, not all projects', () => {
    const projects = [
      makeProject({ projectId: 1, name: 'Alpha' }),
      makeProject({ projectId: 2, name: 'Beta' }),
    ];
    render(<ProjectSummary projects={projects} />);
    const buttons = screen.getAllByTitle('View project progress');
    fireEvent.click(buttons[0]);
    // Only one modal should be open
    expect(screen.getAllByTestId('snapshot-modal')).toHaveLength(1);
  });
});
