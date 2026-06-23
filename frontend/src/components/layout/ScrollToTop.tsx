import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 Resets the viewport scroll to the top whenever the route pathname changes.
**/
export function ScrollToTop(): null {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (hash) return;
    window.scrollTo({ top: 0, left: 0 });
  }, [pathname, hash]);

  return null;
}
