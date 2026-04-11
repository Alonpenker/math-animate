import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { getSystemPrompt } from '@/services/api';
import { JobStateDiagram } from '@/components/create/JobStateDiagram';

export function AboutPage() {
  const [prompt, setPrompt] = useState<string | null>(null);
  const [promptLoading, setPromptLoading] = useState(true);
  const [promptError, setPromptError] = useState(false);

  useEffect(() => {
    getSystemPrompt()
      .then((res) => setPrompt(res.codegen_prompt))
      .catch(() => setPromptError(true))
      .finally(() => setPromptLoading(false));
  }, []);

  return (
    <div className="px-4 py-12">
      <div className="mx-auto max-w-4xl space-y-16">
        <section>
          <h1 className="text-4xl font-semibold text-off-white">About MathAnimate</h1>
          <p className="mt-4 text-off-white/60 leading-relaxed max-w-2xl">
            MathAnimate turns lesson ideas into animated math videos.
            It was built for teachers who want to create visual explanations
            without learning animation tools. Describe your topic in plain
            language, and the system plans, codes, and renders the video for you.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-off-white">Powered by Manim</h2>
          <p className="mt-3 text-off-white/60 leading-relaxed max-w-2xl">
            <a href="https://www.manim.community/" target="_blank" rel="noopener noreferrer"
               className="text-accent-cyan hover:underline">Manim</a> is a Python library
            for creating precise mathematical animations. MathAnimate uses it as the
            rendering engine because it produces clean, publication-quality visuals
            that are ideal for teaching.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-off-white">The Codegen Prompt</h2>
          <p className="mt-3 text-off-white/60 leading-relaxed max-w-2xl mb-4">
            This is the actual system prompt used to generate the Manim Python code for each scene.
            Free to use - take it, tweak it for your own use case.
          </p>
          {promptLoading && <Loader2 className="h-5 w-5 animate-spin text-accent-cyan" />}
          {promptError && <p className="text-off-white/40">Could not load the system prompt.</p>}
          {prompt && (
            <pre className="max-h-96 overflow-auto rounded-lg bg-surface-dark border border-off-white/10 p-4 text-sm text-off-white/80 whitespace-pre-wrap">
              {prompt}
            </pre>
          )}
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-off-white">How the Pipeline Works</h2>
          <p className="mt-3 text-off-white/60 leading-relaxed max-w-2xl mb-6">
            Each lesson goes through a multi-stage pipeline: planning, code generation,
            verification, and rendering. The diagram below shows the full state machine.
          </p>
          <JobStateDiagram currentStatus={null} mode="static" />
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-off-white">Open Source</h2>
          <p className="mt-3 text-off-white/60 leading-relaxed max-w-2xl">
            MathAnimate is fully open source. Contributions, bug reports, and feature
            requests are welcome.
          </p>
          <a href="https://github.com/Alonpenker/math-animate" target="_blank"
             rel="noopener noreferrer"
             className="mt-3 inline-block text-accent-cyan hover:underline">
            View on GitHub →
          </a>
        </section>
      </div>
    </div>
  );
}
