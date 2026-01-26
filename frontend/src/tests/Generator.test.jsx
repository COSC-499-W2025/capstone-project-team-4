import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Generator from '@/pages/Generator';

/* ------------------ mocks ------------------ */

vi.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: vi.fn(),
}));

import { useFileUpload } from '@/hooks/useFileUpload';

vi.mock('@/components/Navigation', () => ({
  default: () => <nav data-testid="navigation">Navigation</nav>,
}));

vi.mock('@/components/custom/Generator/PageHeader', () => ({
  default: ({ title, subtitle }) => (
    <>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </>
  ),
}));

vi.mock('@/components/custom/Generator/UploadSection', () => ({
  default: ({ onFileDrop }) => (
    <button onClick={() => onFileDrop([{ name: 'test.zip' }])}>
      Upload File
    </button>
  ),
}));

vi.mock('@/components/custom/Generator/ConfirmFilesSection', () => ({
  default: ({ files, onDelete, onSubmit, isLoading }) =>
    files.length ? (
      <div data-testid="confirm-section">
        <p>Files: {files.length}</p>
        <button onClick={() => onDelete(0)}>Delete File</button>
        <button onClick={onSubmit} disabled={isLoading}>
          Submit & Analyze
        </button>
      </div>
    ) : null,
}));

vi.mock('@/components/custom/Generator/SummarySection', () => ({
  default: ({ projectData, onUpdateProject }) =>
    projectData ? (
      <div data-testid="summary-section">
        <p>Projects: {projectData.length}</p>
        <button onClick={() => onUpdateProject(0, { name: 'Updated' })}>
          Edit Project
        </button>
      </div>
    ) : null,
}));

vi.mock('@/components/custom/Generator/DataPrivacyConsent', () => ({
  default: ({ isOpen, onAccept }) =>
    isOpen ? (
      <div data-testid="privacy-modal">
        <button onClick={onAccept}>Accept</button>
      </div>
    ) : null,
}));

const renderPage = () =>
  render(
    <BrowserRouter>
      <Generator />
    </BrowserRouter>
  );

/* ------------------ tests ------------------ */

describe('Generator Page', () => {
  let mockState;

  beforeEach(() => {
    mockState = {
      uploadedFiles: [],
      projectData: null,
      isLoading: false,
      showConsent: false,
      setShowConsent: vi.fn(),
      handleFileDrop: vi.fn(files => {
        mockState.uploadedFiles = files;
      }),
      handleDeleteFile: vi.fn(() => {
        mockState.uploadedFiles = [];
      }),
      handleSubmit: vi.fn(cb => cb()),
      handleConsentAccept: vi.fn(() => {
        mockState.projectData = [{}];
        mockState.showConsent = false;
      }),
      processFiles: vi.fn(),
      clearAllData: vi.fn(),
      handleUpdateProject: vi.fn(),
    };

    useFileUpload.mockImplementation(() => mockState);
  });

  it('renders header and navigation', () => {
    renderPage();
    expect(screen.getByText('Resume Generator')).toBeInTheDocument();
    expect(screen.getByTestId('navigation')).toBeInTheDocument();
  });

  it('shows confirm section after upload', () => {
  const { rerender } = renderPage();

  fireEvent.click(screen.getByText('Upload File'));

  // re-render so Generator reads updated mockState.uploadedFiles
  rerender(
    <BrowserRouter>
      <Generator />
    </BrowserRouter>
  );

  expect(screen.getByTestId('confirm-section')).toBeInTheDocument();
});


  it('shows privacy modal on submit', () => {
    renderPage();
    fireEvent.click(screen.getByText('Upload File'));
    mockState.showConsent = true;
    renderPage();
    expect(screen.getByTestId('privacy-modal')).toBeInTheDocument();
  });

  it('shows summary after accepting consent', () => {
    renderPage();
    fireEvent.click(screen.getByText('Upload File'));
    mockState.showConsent = true;
    renderPage();
    fireEvent.click(screen.getByText('Accept'));
    renderPage();
    expect(screen.getByTestId('summary-section')).toBeInTheDocument();
  });

  it('calls clearAllData on restart confirm', () => {
    global.confirm = vi.fn(() => true);
    mockState.uploadedFiles = [{}];
    renderPage();
    fireEvent.click(screen.getByText('Restart'));
    expect(mockState.clearAllData).toHaveBeenCalled();
  });
});
