import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import MainPage from "@/pages/Home/Home";

describe("MainPage Component", () => {
  
  // Test 1: Component renders without crashing
  it("renders without crashing", () => {
    render(<MainPage />);
  });

  // Test 2: Check main heading is present
  it('displays the main hero heading', () => {
    render(<MainPage />)
    const heading = screen.getByRole('heading', { 
      name: /Coding Project Analyzer/i 
    })
    expect(heading).toBeInTheDocument()
  })

  // Test 3: Check hero description is present
  it('displays the hero description text', () => {
    render(<MainPage />)
    const description = screen.getByText(/Upload your project files/i)
    expect(description).toBeInTheDocument()
  })

  // Test 4: Check CTA buttons in hero section
  it('renders Get Started button', () => {
    render(<MainPage />)
    const buttons = screen.getAllByRole('button', { name: /Get Started/i })
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('renders View Examples button', () => {
    render(<MainPage />)
    const button = screen.getByRole('button', { name: /View Examples/i })
    expect(button).toBeInTheDocument()
  })

  // Test 5: Check "How It Works" section
  it('displays the How It Works section heading', () => {
    render(<MainPage />)
    const heading = screen.getByRole('heading', { name: /How It Works/i })
    expect(heading).toBeInTheDocument()
  })

  // Test 6: Check all three steps are displayed
  it('displays all three steps in the process', () => {
    render(<MainPage />)
    
    expect(screen.getByText(/Upload Your Projects/i)).toBeInTheDocument()
    expect(screen.getByText(/Review & Customize/i)).toBeInTheDocument()
    expect(screen.getByText(/Generate Your Resume/i)).toBeInTheDocument()
  })

  // Test 7: Check step numbers are displayed
  it('displays step numbers 1, 2, and 3', () => {
    render(<MainPage />)
    
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  // Test 8: Check step descriptions
  it('displays step 1 description about uploading zip files', () => {
    render(<MainPage />)
    expect(screen.getByText(/Upload zip files containing your project folders/i)).toBeInTheDocument()
  })

  it('displays step 2 description about customization', () => {
    render(<MainPage />)
    expect(screen.getByText(/Our intelligent system extracts your skills/i)).toBeInTheDocument()
  })

  it('displays step 3 description about generating resume', () => {
    render(<MainPage />)
    expect(screen.getByText(/Click "Start Building Now" to generate/i)).toBeInTheDocument()
  })

  // Test 9: Check CTA section
  it('displays the Ready to Create Your Resume CTA heading', () => {
    render(<MainPage />)
    const heading = screen.getByRole('heading', { name: /Ready to Create Your Resume/i })
    expect(heading).toBeInTheDocument()
  })

  it('displays the Start Building Now button in CTA section', () => {
    render(<MainPage />)
    const buttons = screen.getAllByRole('button', { name: /Start Building Now/i })
    expect(buttons.length).toBeGreaterThan(0)
  })

  // Test 10: Check Features section
  it('displays the Powerful Features section heading', () => {
    render(<MainPage />)
    const heading = screen.getByRole('heading', { name: /Powerful Features for Your Career Success/i })
    expect(heading).toBeInTheDocument()
  })

  // Test 11: Check all feature titles are present
  it('displays all six feature titles', () => {
    render(<MainPage />)
    
    expect(screen.getByText(/Intelligent Analysis/i)).toBeInTheDocument()
    expect(screen.getByText(/Privacy First/i)).toBeInTheDocument()
    expect(screen.getByText(/Smart Ranking/i)).toBeInTheDocument()
    expect(screen.getByText(/Full Customization/i)).toBeInTheDocument()
    expect(screen.getByText(/Track Your Progress/i)).toBeInTheDocument()
    expect(screen.getByText(/Professional Format/i)).toBeInTheDocument()
  })

  // Test 12: Check that MainNav is rendered
  it('renders the MainNav component', () => {
    render(<MainPage />)
    // This assumes MainNav has identifiable content like "Home" or "Login"
    // Adjust based on your actual MainNav implementation
    expect(screen.getByText(/Home/i)).toBeInTheDocument()
  })

  // Test 13: Check for no ATS terminology (requirement from conversation)
  it('does not contain ATS terminology', () => {
    render(<MainPage />)
    const pageText = screen.getByText(/Transform your work history into a professional resume that highlights your best contributions./i).closest('div')?.textContent || ''
    expect(pageText.toLowerCase()).not.toContain('ats')
  })

  // Test 14: Accessibility - check for proper heading hierarchy
  it('has proper heading hierarchy', () => {
    render(<MainPage />)
    const h1 = screen.getByRole('heading', { level: 1 })
    const h2s = screen.getAllByRole('heading', { level: 2 })
    const h3s = screen.getAllByRole('heading', { level: 3 })
    
    expect(h1).toBeInTheDocument()
    expect(h2s.length).toBeGreaterThan(0)
    expect(h3s.length).toBeGreaterThan(0)
  })

  // Test 15: Check responsive container classes
  it('has responsive container classes', () => {
    const { container } = render(<MainPage />)
    const sections = container.querySelectorAll('section')
    
    sections.forEach(section => {
      expect(section.className).toMatch(/container|mx-auto/)
    })
  })
})
