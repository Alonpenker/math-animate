import { Link } from 'react-router-dom';

export function AboutSection() {
  return (
    <section className="px-6 py-16">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="text-2xl font-semibold text-off-white mb-4">About MathAnimate</h2>
        <p className="text-off-white/60 leading-relaxed">
          MathAnimate is an open-source website that turns math lesson briefs into animated videos.
          Powered by{' '}
          <a href="https://www.manim.community/" target="_blank" rel="noopener noreferrer" className="text-accent-orange hover:underline">
            Manim
          </a>
          , it generates scene-by-scene animations that teachers and students can use right away.
        </p>
        <div className="mt-4 flex items-center justify-center gap-6">
          <a
            href="https://github.com/Alonpenker/math-animate"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-off-white/40 hover:text-off-white/60 transition-colors"
          >
            View on GitHub →
          </a>
          <Link
            to="/about"
            className="text-sm text-off-white/40 hover:text-off-white/60 transition-colors"
          >
            How it works →
          </Link>
        </div>
      </div>
    </section>
  );
}
