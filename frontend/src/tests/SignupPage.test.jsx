import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import SignupPage from "@/pages/auth/signup";

describe("SignupPage Component", () => {
    // Test 1: Component renders without crashing
    it("renders without crashing", () => {
        render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );
    });

    // Test 2: Check heading is present
    it("displays the Sign up heading", () => {
        render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );

        const heading = screen.getByRole("heading", { name: /Sign up/i });
        expect(heading).toBeInTheDocument();
    });

    // Test 3: Check key inputs exist
    it("renders full name, email, password, and confirm fields", () => {
        render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );

        expect(screen.getByLabelText(/Full name/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/^Email$/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Confirm/i)).toBeInTheDocument();
    });

    // Test 4: Check terms checkbox exists
    it("renders the terms agreement checkbox", () => {
        render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );

        // shadcn checkbox typically renders role="checkbox"
        const checkbox = screen.getByRole("checkbox");
        expect(checkbox).toBeInTheDocument();
    });

    // Test 5: Check primary CTA exists
    it("renders Create account button", () => {
        render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );

        const button = screen.getByRole("button", { name: /Create account/i });
        expect(button).toBeInTheDocument();
    });

    // Test 6: Check link back to login exists
    it("renders Sign in link", () => {
        render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );

        const link = screen.getByRole("link", { name: /Sign in/i });
        expect(link).toBeInTheDocument();
        expect(link.getAttribute("href")).toBe("/login");
    });

    // Test 7: Check MainNav is rendered (assumes it contains Home)
    it("renders the MainNav component", () => {
        render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );

        expect(screen.getByText(/Home/i)).toBeInTheDocument();
    });

    // Test 8: Accessibility - check headings exist
    it("has proper headings", () => {
        render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );

        const headings = screen.getAllByRole("heading");
        expect(headings.length).toBeGreaterThan(0);
    });

    // Test 9: Check responsive container classes (similar to Home test)
    it("has responsive container classes", () => {
        const { container } = render(
        <MemoryRouter>
            <SignupPage />
        </MemoryRouter>
        );

        const autoContainers = container.querySelectorAll("[class*='mx-auto']");
        expect(autoContainers.length).toBeGreaterThan(0);
    });
});
