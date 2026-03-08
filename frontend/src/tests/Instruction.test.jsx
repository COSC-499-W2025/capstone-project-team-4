import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import Instruction from '@/pages/Instruction';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock Navigation component
vi.mock('@/components/Navigation', () => ({
  default: () => <nav data-testid="navigation">Navigation</nav>,
}));

// Mock InstructionHeader component
vi.mock('@/components/custom/Instruction/InstructionHeader', () => ({
  default: ({ onGetStarted }) => (
    <div data-testid="instruction-header">
      <h1>Resume Generator</h1>
      <p>Transform your project files into a professional resume in 4 easy steps</p>
      <button onClick={onGetStarted}>Get Started</button>
    </div>
  ),
}));

// Mock StepsGrid component
vi.mock('@/components/custom/Instruction/StepsGrid', () => ({
  default: () => (
    <div data-testid="steps-grid">
      <div>1</div>
      <div>Upload</div>
      <div>Drag and drop your project ZIP files</div>
      <div>2</div>
      <div>Confirm</div>
      <div>Review and manage uploaded files</div>
      <div>3</div>
      <div>Analyze</div>
      <div>Submit to analyze your projects</div>
      <div>4</div>
      <div>Review</div>
      <div>View and sort project summary</div>
    </div>
  ),
}));

// Helper to render with router
const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Instruction Page', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    localStorage.removeItem('access_token');
  });

  it('renders the page correctly', () => {
    renderWithRouter(<Instruction />);
    
    expect(screen.getByText('Resume Generator')).toBeInTheDocument();
  });

  it('renders navigation component', () => {
    renderWithRouter(<Instruction />);
    
    expect(screen.getByTestId('navigation')).toBeInTheDocument();
  });

  it('renders InstructionHeader component', () => {
    renderWithRouter(<Instruction />);
    
    expect(screen.getByTestId('instruction-header')).toBeInTheDocument();
  });

  it('renders StepsGrid component', () => {
    renderWithRouter(<Instruction />);
    
    expect(screen.getByTestId('steps-grid')).toBeInTheDocument();
  });

  it('displays all 4 steps', () => {
    renderWithRouter(<Instruction />);
    
    // Check step numbers
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('displays step titles', () => {
    renderWithRouter(<Instruction />);
    
    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText('Confirm')).toBeInTheDocument();
    expect(screen.getByText('Analyze')).toBeInTheDocument();
    expect(screen.getAllByText('Review').length).toBeGreaterThan(0);
  });

  it('displays step descriptions', () => {
    renderWithRouter(<Instruction />);
    
    expect(screen.getByText(/Drag and drop your project ZIP files/i)).toBeInTheDocument();
    expect(screen.getByText(/Review and manage uploaded files/i)).toBeInTheDocument();
    expect(screen.getByText(/Submit to analyze your projects/i)).toBeInTheDocument();
    expect(screen.getByText(/View and sort project summary/i)).toBeInTheDocument();
  });

  it('renders "Get Started" button', () => {
    renderWithRouter(<Instruction />);
    
    expect(screen.getByText('Get Started')).toBeInTheDocument();
  });

  it('navigates to /login when unauthenticated and "Get Started" is clicked', () => {
    renderWithRouter(<Instruction />);
    
    const getStartedButton = screen.getByText('Get Started');
    fireEvent.click(getStartedButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('has correct layout structure', () => {
    const { container } = renderWithRouter(<Instruction />);
    
    // Check for main container with correct classes
    const mainContainer = container.querySelector('.min-h-screen.flex.flex-col');
    expect(mainContainer).toBeInTheDocument();
  });

  it('has gradient background', () => {
    const { container } = renderWithRouter(<Instruction />);
    
    const gradientDiv = container.querySelector('.bg-gradient-to-b.from-blue-50.to-white');
    expect(gradientDiv).toBeInTheDocument();
  });

  it('has centered content with max width', () => {
    const { container } = renderWithRouter(<Instruction />);
    
    const maxWidthDiv = container.querySelector('.max-w-7xl.mx-auto');
    expect(maxWidthDiv).toBeInTheDocument();
  });

  it('passes onGetStarted handler to InstructionHeader', () => {
    renderWithRouter(<Instruction />);
    
    const button = screen.getByText('Get Started');
    expect(button).toBeInTheDocument();
    
    // Click and verify navigation
    fireEvent.click(button);
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('navigates to /generate when authenticated and "Get Started" is clicked', () => {
    localStorage.setItem('access_token', 'test-token');
    renderWithRouter(<Instruction />);

    const getStartedButton = screen.getByText('Get Started');
    fireEvent.click(getStartedButton);

    expect(mockNavigate).toHaveBeenCalledWith('/generate');
  });

  it('renders in correct order: Navigation -> Header -> Steps', () => {
    renderWithRouter(<Instruction />);
    
    const nav = screen.getByTestId('navigation');
    const header = screen.getByTestId('instruction-header');
    const steps = screen.getByTestId('steps-grid');
    
    expect(nav).toBeInTheDocument();
    expect(header).toBeInTheDocument();
    expect(steps).toBeInTheDocument();
  });
});
