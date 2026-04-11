import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/create', label: 'Create' },
  { to: '/jobs', label: 'Jobs' },
  { to: '/lessons', label: 'Lessons' },
  { to: '/usage', label: 'Usage' },
  { to: '/about', label: 'About' },
] as const;

export function GlassNavbar() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
      style={{
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        WebkitBackdropFilter: scrolled ? 'blur(12px)' : 'none',
        background: scrolled ? 'rgba(15,15,15,0.65)' : 'transparent',
        borderBottom: scrolled ? '1px solid rgba(255,255,255,0.1)' : '1px solid transparent',
        padding: '14px 0',
      }}
    >
      <div className="relative flex items-center px-8">
        <Link
          to="/"
          className="flex items-center gap-2 text-lg font-bold text-off-white no-underline shrink-0"
          style={{ letterSpacing: '0.01em' }}
        >
          <img src="/MathAnimate-Icon.png" alt="" className="h-9 w-auto" />
          <span>
            Math<span className="text-accent-orange">Animate</span>
          </span>
        </Link>

        <div
          className="hidden md:flex items-center gap-12"
          style={{
            position: 'absolute',
            left: '50%',
            transform: 'translateX(-50%)',
          }}
        >
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`text-base no-underline transition-colors duration-200 pb-0.5 ${
                isActive(link.to)
                  ? 'text-accent-orange border-b border-accent-orange'
                  : 'text-off-white/70 hover:text-off-white'
              }`}
             
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="flex-1" />

        <div className="md:hidden">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger
              className="rounded p-1 text-off-white hover:bg-white/10"
              aria-label="Open menu"
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </SheetTrigger>
            <SheetContent
              side="right"
              className="w-64"
              style={{ background: 'rgba(15,15,15,0.95)', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
              <div className="mt-10 flex flex-col gap-3">
                {NAV_LINKS.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    onClick={() => setOpen(false)}
                    className={`block rounded-lg px-3 py-2 text-sm no-underline ${
                      isActive(link.to)
                        ? 'bg-white/10 text-accent-orange'
                        : 'text-off-white/70 hover:bg-white/5 hover:text-off-white'
                    }`}
                   
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </nav>
  );
}
