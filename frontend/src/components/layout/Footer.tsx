import { FaGithub, FaLinkedin } from 'react-icons/fa';

export function Footer() {
  return (
    <footer
      className="py-8 text-center"
      style={{
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        background: 'rgba(15,15,15,0.55)',
        borderTop: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      <p className="text-sm text-chalk-white/50" style={{ fontFamily: 'Inter, sans-serif' }}>
        This project is by Alon Penker
      </p>
      <div className="mt-3 flex items-center justify-center gap-5">
        <a
          href="https://github.com/Alonpenker"
          target="_blank"
          rel="noopener noreferrer"
          className="text-chalk-white/50 transition-colors hover:text-chalk-cyan"
          aria-label="GitHub profile"
        >
          <FaGithub className="h-5 w-5" />
        </a>
        <a
          href="https://www.linkedin.com/in/alon-penker/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-chalk-white/50 transition-colors hover:text-chalk-cyan"
          aria-label="LinkedIn profile"
        >
          <FaLinkedin className="h-5 w-5" />
        </a>
      </div>
    </footer>
  );
}
