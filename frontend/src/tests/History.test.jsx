import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('@/lib/auth', () => ({
  getAccessToken: () => 'fake-token',
}));

vi.mock('@/components/Navigation', () => ({
  default: () => <nav data-testid="navigation" />,
}));

vi.mock('@/components/custom/Generator/ProjectSummary', () => ({
  default: ({ projects, onDeleteProject }) => (
    <div data-testid="project-summary">
      {projects.map((p) => (
        <div key={p.projectId} data-testid="project-card">
          <span>{p.name}</span>
          <button onClick={() => onDeleteProject(p.projectId)}>Delete {p.name}</button>
        </div>
      ))}
    </div>
  ),
}));

import axios from 'axios';
import HistoryPage from '@/pages/History';

const makeDetail = (overrides = {}) => ({
  id: 1,
  name: 'Sample Project',
  file_count: 5,
  created_at: '2025-01-01T00:00:00Z',
  zip_uploaded_at: '2025-01-01T00:00:00Z',
  project_started_at: null,
  first_commit_date: null,
  first_file_created: null,
  languages: ['Python'],
  frameworks: [],
  libraries: [],
  tools: [],
  total_lines_of_code: 300,
  avg_complexity: 2.0,
  max_complexity: 6,
  contributor_count: 1,
  library_count: 0,
  tool_count: 0,
  ...overrides,
});

// Mock GET /api/projects (list) + N detail calls for the given projects array
function mockProjectList(projectsData) {
  const items = projectsData.map((p) => ({ id: p.id }));
  axios.get.mockResolvedValueOnce({ data: { items } });
  projectsData.forEach((p) => {
    axios.get.mockResolvedValueOnce({ data: makeDetail(p) });
  });
}

describe('History Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    axios.delete.mockResolvedValue({});
  });

  // ── Loading / error / empty states ────────────────────────────────────────

  it('renders the navigation', async () => {
    axios.get.mockResolvedValue({ data: { items: [] } });
    render(<HistoryPage />);
    expect(screen.getByTestId('navigation')).toBeInTheDocument();
  });

  it('shows a loading spinner while fetching', () => {
    axios.get.mockReturnValue(new Promise(() => {}));
    render(<HistoryPage />);
    expect(screen.getByText(/Loading your projects/i)).toBeInTheDocument();
  });

  it('shows an error message when the API call fails', async () => {
    axios.get.mockRejectedValue({ message: 'Network Error' });
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Network Error')).toBeInTheDocument();
    });
  });

  it('shows the empty state when there are no projects', async () => {
    axios.get.mockResolvedValue({ data: { items: [] } });
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText(/No projects yet/i)).toBeInTheDocument();
    });
  });

  it('renders the page heading', async () => {
    axios.get.mockResolvedValue({ data: { items: [] } });
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Project History')).toBeInTheDocument();
    });
  });

  it('shows the total project count badge', async () => {
    mockProjectList([
      { id: 1, name: 'A' },
      { id: 2, name: 'B' },
    ]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('renders project cards once data has loaded', async () => {
    mockProjectList([{ id: 1, name: 'My Project' }]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('My Project')).toBeInTheDocument();
    });
  });

  // ── Pagination — visibility ───────────────────────────────────────────────

  it('does not show pagination controls when there are 6 or fewer projects', async () => {
    mockProjectList(
      Array.from({ length: 6 }, (_, i) => ({ id: i + 1, name: `P${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('P1')).toBeInTheDocument();
    });
    expect(screen.queryByRole('navigation', { name: /pagination/i })).not.toBeInTheDocument();
  });

  it('shows pagination controls when there are more than 6 projects', async () => {
    mockProjectList(
      Array.from({ length: 7 }, (_, i) => ({ id: i + 1, name: `P${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
    });
  });

  // ── Pagination — page size ────────────────────────────────────────────────

  it('shows at most 6 projects on the first page', async () => {
    mockProjectList(
      Array.from({ length: 9 }, (_, i) => ({ id: i + 1, name: `Project ${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(6);
    });
  });

  it('shows remaining projects on page 2', async () => {
    mockProjectList(
      Array.from({ length: 9 }, (_, i) => ({ id: i + 1, name: `Project ${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Go to next page'));

    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(3);
    });
  });

  // ── Pagination — navigation controls ────────────────────────────────────

  it('navigates to a specific page when a page number is clicked', async () => {
    mockProjectList(
      Array.from({ length: 13 }, (_, i) => ({ id: i + 1, name: `Project ${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('2'));

    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(6);
    });
    // Page 2 link should now be active
    expect(screen.getByText('2').closest('[data-active="true"]')).toBeTruthy();
  });

  it('previous button is disabled on the first page', async () => {
    mockProjectList(
      Array.from({ length: 7 }, (_, i) => ({ id: i + 1, name: `P${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByLabelText('Go to previous page')).toBeInTheDocument();
    });
    expect(screen.getByLabelText('Go to previous page').closest('li').querySelector('a'))
      .toHaveClass('opacity-50');
  });

  it('next button is disabled on the last page', async () => {
    mockProjectList(
      Array.from({ length: 7 }, (_, i) => ({ id: i + 1, name: `P${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Go to next page'));

    await waitFor(() => {
      expect(screen.getByLabelText('Go to next page').closest('li').querySelector('a'))
        .toHaveClass('opacity-50');
    });
  });

  // ── Delete behaviour ──────────────────────────────────────────────────────

  it('removes a project from the list when deleted', async () => {
    mockProjectList([
      { id: 1, name: 'Keep Me' },
      { id: 2, name: 'Delete Me' },
    ]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Delete Me')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Delete Delete Me'));

    await waitFor(() => {
      expect(screen.queryByText('Delete Me')).not.toBeInTheDocument();
    });
    expect(screen.getByText('Keep Me')).toBeInTheDocument();
  });

  it('calls the DELETE API with the correct project id', async () => {
    mockProjectList([{ id: 42, name: 'Target' }]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Target')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Delete Target'));

    expect(axios.delete).toHaveBeenCalledWith(
      '/api/projects/42',
      expect.objectContaining({ headers: { Authorization: 'Bearer fake-token' } })
    );
  });

  it('goes back to the previous page when the last project on a page is deleted', async () => {
    // 7 projects: 6 on page 1, 1 on page 2
    mockProjectList(
      Array.from({ length: 7 }, (_, i) => ({ id: i + 1, name: `Project ${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
    });

    // Navigate to page 2
    fireEvent.click(screen.getByLabelText('Go to next page'));
    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(1);
    });

    // Delete the only project on page 2
    fireEvent.click(screen.getByText('Delete Project 7'));

    await waitFor(() => {
      // Should have jumped back to page 1 with 6 projects
      expect(screen.getAllByTestId('project-card')).toHaveLength(6);
    });
  });

  it('shows an alert and keeps the project when deletion fails', async () => {
    vi.stubGlobal('alert', vi.fn());
    axios.delete.mockRejectedValue({ message: 'Server error' });
    mockProjectList([{ id: 1, name: 'Survivor' }]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Survivor')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Delete Survivor'));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalled();
    });
    expect(screen.getByText('Survivor')).toBeInTheDocument();
  });

  // ── Search behaviour ──────────────────────────────────────────────────────

  it('renders the search input when projects are loaded', async () => {
    mockProjectList([{ id: 1, name: 'Alpha' }]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search projects by name/i)).toBeInTheDocument();
    });
  });

  it('filters project cards by search query', async () => {
    mockProjectList([
      { id: 1, name: 'Alpha Project' },
      { id: 2, name: 'Beta Project' },
      { id: 3, name: 'Gamma Project' },
    ]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(3);
    });

    fireEvent.change(screen.getByPlaceholderText(/search projects by name/i), {
      target: { value: 'Alpha' },
    });

    expect(screen.getAllByTestId('project-card')).toHaveLength(1);
    expect(screen.getByText('Alpha Project')).toBeInTheDocument();
    expect(screen.queryByText('Beta Project')).not.toBeInTheDocument();
  });

  it('shows the no-results empty state when search matches nothing', async () => {
    mockProjectList([{ id: 1, name: 'Alpha Project' }]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Alpha Project')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText(/search projects by name/i), {
      target: { value: 'zzz-no-match' },
    });

    expect(screen.queryByTestId('project-card')).not.toBeInTheDocument();
    expect(screen.getByText(/no projects match/i)).toBeInTheDocument();
  });

  it('shows "X of Y" count badge when a search is active', async () => {
    mockProjectList([
      { id: 1, name: 'Alpha' },
      { id: 2, name: 'Beta' },
    ]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(2);
    });

    fireEvent.change(screen.getByPlaceholderText(/search projects by name/i), {
      target: { value: 'Alpha' },
    });

    expect(screen.getByText('1 of 2')).toBeInTheDocument();
  });

  it('resets to page 1 when the search query changes', async () => {
    mockProjectList(
      Array.from({ length: 9 }, (_, i) => ({ id: i + 1, name: `Project ${i + 1}` }))
    );
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
    });

    // Navigate to page 2
    fireEvent.click(screen.getByLabelText('Go to next page'));
    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(3);
    });

    // Typing in the search should reset back to page 1
    fireEvent.change(screen.getByPlaceholderText(/search projects by name/i), {
      target: { value: 'Project' },
    });

    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(6);
    });
  });

  // ── Delete All behaviour ──────────────────────────────────────────────────

  it('shows the Delete All button when projects are loaded', async () => {
    mockProjectList([{ id: 1, name: 'Alpha' }]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText(/delete all/i)).toBeInTheDocument();
    });
  });

  it('shows confirm and cancel buttons after clicking Delete All', async () => {
    mockProjectList([{ id: 1, name: 'Alpha' }]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText(/delete all/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/delete all/i));

    expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('hides the confirmation and keeps projects when Cancel is clicked', async () => {
    mockProjectList([
      { id: 1, name: 'Alpha' },
      { id: 2, name: 'Beta' },
    ]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText(/delete all/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/delete all/i));
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

    expect(screen.queryByRole('button', { name: /confirm/i })).not.toBeInTheDocument();
    expect(screen.getAllByTestId('project-card')).toHaveLength(2);
  });

  it('calls DELETE for every project when Delete All is confirmed', async () => {
    mockProjectList([
      { id: 1, name: 'Alpha' },
      { id: 2, name: 'Beta' },
    ]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText(/delete all/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/delete all/i));
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(axios.delete).toHaveBeenCalledWith(
        '/api/projects/1',
        expect.objectContaining({ headers: { Authorization: 'Bearer fake-token' } })
      );
      expect(axios.delete).toHaveBeenCalledWith(
        '/api/projects/2',
        expect.objectContaining({ headers: { Authorization: 'Bearer fake-token' } })
      );
    });
  });

  it('clears the project list after Delete All is confirmed', async () => {
    mockProjectList([
      { id: 1, name: 'Alpha' },
      { id: 2, name: 'Beta' },
    ]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getAllByTestId('project-card')).toHaveLength(2);
    });

    fireEvent.click(screen.getByText(/delete all/i));
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(screen.getByText(/no projects yet/i)).toBeInTheDocument();
    });
  });

  it('shows an alert and keeps projects when Delete All fails', async () => {
    vi.stubGlobal('alert', vi.fn());
    axios.delete.mockRejectedValue({ message: 'Server error' });
    mockProjectList([{ id: 1, name: 'Alpha' }]);
    render(<HistoryPage />);
    await waitFor(() => {
      expect(screen.getByText(/delete all/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/delete all/i));
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalled();
    });
    expect(screen.getByText('Alpha')).toBeInTheDocument();
  });
});
