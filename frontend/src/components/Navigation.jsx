import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Home, Sparkles } from 'lucide-react';
import { clearAccessToken, isAuthenticated } from '@/lib/auth';

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [authed, setAuthed] = React.useState(isAuthenticated());

  React.useEffect(() => {
    const syncAuthState = () => setAuthed(isAuthenticated());
    window.addEventListener('storage', syncAuthState);
    window.addEventListener('focus', syncAuthState);
    return () => {
      window.removeEventListener('storage', syncAuthState);
      window.removeEventListener('focus', syncAuthState);
    };
  }, []);

  const handleLogout = () => {
    clearAccessToken();
    setAuthed(false);
    navigate('/login');
  };

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex space-x-8">
            {/* Logo/Brand */}
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                Resume Generator
              </h1>
            </div>
            
            {/* Navigation Links */}
            <div className="hidden sm:ml-6 sm:flex sm:space-x-4">
              <Link to="/">
                <Button
                  variant={location.pathname === '/' ? 'default' : 'ghost'}
                  className="flex items-center space-x-2"
                >
                  <Home className="h-4 w-4" />
                  <span>Home</span>
                </Button>
              </Link>
              
              <Link to="/generate">
                <Button
                  variant={location.pathname === '/generate' ? 'default' : 'ghost'}
                  className="flex items-center space-x-2"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>Generate</span>
                </Button>
              </Link>

              {authed ? (
                <Button variant="ghost" onClick={handleLogout}>
                  Logout
                </Button>
              ) : (
                <Link to="/login">
                  <Button
                    variant={location.pathname === '/login' ? 'default' : 'ghost'}
                    className="flex items-center space-x-2"
                  >
                    <span>Login</span>
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;