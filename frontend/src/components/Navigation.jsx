import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

import { FileText, Home, Sparkles, User, LayoutDashboard, UserPlus, History } from "lucide-react";
import { clearAccessToken, isAuthenticated } from "@/lib/auth";

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [authed, setAuthed] = React.useState(isAuthenticated());

  React.useEffect(() => {
    const syncAuthState = () => setAuthed(isAuthenticated());
    window.addEventListener("storage", syncAuthState);
    window.addEventListener("focus", syncAuthState);
    return () => {
      window.removeEventListener("storage", syncAuthState);
      window.removeEventListener("focus", syncAuthState);
    };
  }, []);

  const handleLogout = () => {
    clearAccessToken();
    setAuthed(false);
    navigate("/login");
  };

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* Left: Brand + main nav links */}
          <div className="flex items-center">
            <div className="flex-shrink-0 mr-4">
              <h1 className="text-lg font-bold text-gray-900">
                Coding Project Analyzer
              </h1>
            </div>

            <div className="hidden sm:flex sm:items-center sm:space-x-1">
              <Link to="/">
                <Button
                  variant={location.pathname === "/" ? "default" : "ghost"}
                  size="sm"
                  className="flex items-center space-x-1"
                >
                  <Home className="h-4 w-4" />
                  <span>Home</span>
                </Button>
              </Link>

              <Link to="/generate">
                <Button
                  variant={location.pathname === "/generate" ? "default" : "ghost"}
                  size="sm"
                  className="flex items-center space-x-1"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>Generate</span>
                </Button>
              </Link>

              {authed && (
                <Link to="/history">
                  <Button
                    variant={location.pathname === "/history" ? "default" : "ghost"}
                    size="sm"
                    className="flex items-center space-x-1"
                  >
                    <History className="h-4 w-4" />
                    <span>History</span>
                  </Button>
                </Link>
              )}

              {authed && (
                <Link to="/resume-builder">
                  <Button
                    variant={location.pathname === "/resume-builder" ? "default" : "ghost"}
                    size="sm"
                    className="flex items-center space-x-1"
                  >
                    <FileText className="h-4 w-4" />
                    <span>Resume Builder</span>
                  </Button>
                </Link>
              )}

              {authed && (
                <Link to="/portfolio">
                  <Button
                    variant={location.pathname === "/portfolio" ? "default" : "ghost"}
                    size="sm"
                    className="flex items-center space-x-1"
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    <span>Portfolio</span>
                  </Button>
                </Link>
              )}
            </div>
          </div>

          {/* Right: Account / auth actions */}
          <div className="flex items-center space-x-1">
            {authed ? (
              <>
                <Link to="/account">
                  <Button
                    variant={location.pathname === "/account" ? "default" : "ghost"}
                    size="sm"
                    className="flex items-center space-x-1"
                  >
                    <User className="h-4 w-4" />
                    <span>Account</span>
                  </Button>
                </Link>
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link to="/signup">
                  <Button
                    variant={location.pathname === "/signup" ? "default" : "ghost"}
                    size="sm"
                    className="flex items-center space-x-1"
                  >
                    <UserPlus className="h-4 w-4" />
                    <span>Register</span>
                  </Button>
                </Link>
                <Link to="/login">
                  <Button
                    variant={location.pathname === "/login" ? "default" : "ghost"}
                    size="sm"
                  >
                    Login
                  </Button>
                </Link>
              </>
            )}
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navigation;
