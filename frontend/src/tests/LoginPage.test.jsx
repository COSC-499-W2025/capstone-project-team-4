import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import LoginPage from "@/pages/auth/login";

describe("LoginPage Component", () => {
    // Test 1: Component renders without crashing
    it("renders without crashing", () => {
        render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );
    });

    // Test 2: Check main heading is present (form focus)
    it("displays the Log in heading", () => {
        render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );

        const heading = screen.getByRole("heading", { name: /Log in/i });
        expect(heading).toBeInTheDocument();
    });

    // Test 3: Check email and password labels exist
    it("renders email and password fields", () => {
        render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );

        expect(screen.getByLabelText(/^Email$/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    });

    // Test 4: Check primary button exists
    it("renders Sign in button", () => {
        render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );

        const button = screen.getByRole("button", { name: /Sign in/i });
        expect(button).toBeInTheDocument();
    });

    // Test 5: Check link to signup exists
    it("renders Create an account link", () => {
        render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );

        const link = screen.getByRole("link", { name: /Create an account/i });
        expect(link).toBeInTheDocument();
        expect(link.getAttribute("href")).toBe("/signup");
    });

    // Test 6: Check MainNav is rendered (assumes it contains Home/Login)
    it("renders the MainNav component", () => {
        render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );

        expect(screen.getByText(/Home/i)).toBeInTheDocument();
    });

    // Test 7: Accessibility - required heading exists
    it("has a primary heading", () => {
        render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );

        const headings = screen.getAllByRole("heading");
        expect(headings.length).toBeGreaterThan(0);
    });

    // Test 8: Forgot password button should be present
    it("renders a Forgot password button", () => {
        render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );

        expect(screen.getByText(/Forgot password/i)).toBeInTheDocument();
    });

    // Test 9: Check responsive container classes (similar idea to your Home test)
    it("has responsive container classes", () => {
        const { container } = render(
        <MemoryRouter>
            <LoginPage />
        </MemoryRouter>
        );

        // AuthShell uses wrappers; we expect at least one mx-auto container present.
        expect(container.textContent).toBeTruthy();
        const autoContainers = container.querySelectorAll("[class*='mx-auto']");
        expect(autoContainers.length).toBeGreaterThan(0);
    });
});
