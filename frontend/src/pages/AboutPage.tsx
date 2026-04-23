import { useQuery } from '@tanstack/react-query';

import { getSystemPrompt } from '@/services/api';
import { JobStateDiagram } from '@/components/create/JobStateDiagram';
import { InfoSection, SectionText } from '@/components/about/InfoSection';
import { PromptView, SkeletonPromptView } from '@/components/about/PromptView';

export function AboutPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['system-prompt'],
    queryFn: getSystemPrompt,
  });


  return (
    <div className="px-4 py-12">
      <div className="mx-auto max-w-4xl space-y-16">

        <InfoSection title="About MathAnimate">
          <SectionText>
            MathAnimate turns lesson ideas into animated math videos.
            It was built for teachers who want to create visual explanations
            without learning animation tools. Describe your topic in plain
            language, and the system plans, codes, and renders the video for you.
          </SectionText>
        </InfoSection>
        
        <InfoSection title="Powered by Manim">
          <SectionText>
            <a href="https://www.manim.community/" target="_blank" rel="noopener noreferrer"
              className="text-accent-cyan hover:underline">Manim</a> is a Python library
              for creating precise mathematical animations. MathAnimate uses it as the
              rendering engine because it produces clean, publication-quality visuals
              that are ideal for teaching.
          </SectionText>
        </InfoSection>
        
        <InfoSection title="The Codegen Prompt">
          {isLoading ? (
            <SkeletonPromptView />
          ) : isError || !data ? (
            <SectionText>Could not load the system prompt right now, try again later.</SectionText>
          ) : (
            <PromptView prompt={data.codegen_prompt} />
          )}
        </InfoSection>
        
        <InfoSection title="How the Pipeline Works">
          <SectionText>
            Each lesson goes through a multi-stage pipeline: planning, code generation,
            verification, and rendering. The diagram below shows the full state machine.
          </SectionText>
          <JobStateDiagram currentStatus={null} mode="static" />
        </InfoSection>
        
        <InfoSection title="Open Source">
          <SectionText>
             MathAnimate is fully open source. Contributions, bug reports, and feature
            requests are welcome.
          </SectionText>
          <a href="https://github.com/Alonpenker/math-animate" target="_blank"
             rel="noopener noreferrer"
             className="mt-3 inline-block text-accent-cyan hover:underline">
            View on GitHub →
          </a>
        </InfoSection>

      </div>
    </div>
  );
}
