import { FaGithub, FaLinkedin } from 'react-icons/fa';

export function Footer() {
  return (
    <footer className="border-t border-brand-border py-6 text-center text-brand-muted">
      <p className="text-sm">This project is by Alon Penker</p>
      <div className="mt-2 flex items-center justify-center gap-4">
        <a
          href="https://github.com/Alonpenker"
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-muted transition-colors hover:text-brand"
          aria-label="GitHub profile"
        >
          <FaGithub className="h-5 w-5" />
        </a>
        <a
          href="https://www.linkedin.com/in/alon-penker/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-muted transition-colors hover:text-brand-light"
          aria-label="LinkedIn profile"
        >
          <FaLinkedin className="h-5 w-5" />
        </a>
      </div>
    </footer>
  );
}
