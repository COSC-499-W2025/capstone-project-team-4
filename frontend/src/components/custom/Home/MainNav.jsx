import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";

export default function MainNav() {
  return (
    <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-end">
          <NavigationMenu>
            <NavigationMenuList className="flex gap-8 py-4">
              {/* Home */}
              <NavigationMenuItem>
                <NavigationMenuLink
                  href="/"
                  className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-slate-900 after:transition-all"
                >
                  Home
                </NavigationMenuLink>
              </NavigationMenuItem>
              {/* User Profiles */}
              <NavigationMenuItem>
                <NavigationMenuLink
                  href="/profiles"
                  className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-slate-900 after:transition-all"
                >
                  User Profiles
                </NavigationMenuLink>
              </NavigationMenuItem>
              {/* Login */}
              <NavigationMenuItem>
                <NavigationMenuLink
                  href="/login"
                  className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-slate-900 after:transition-all"
                >
                  Login
                </NavigationMenuLink>
              </NavigationMenuItem>
              {/* Analysis */}
              <NavigationMenuItem>
                <NavigationMenuLink
                  href="/analysis"
                  className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-slate-900 after:transition-all"
                >
                  Analysis
                </NavigationMenuLink>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        </div>
      </div>
    </nav>
  );
}