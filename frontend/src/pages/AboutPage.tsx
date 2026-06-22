import { InfoSection, SectionText } from '@/components/about/InfoSection';
import { WorkflowDataFlow } from '@/components/about/WorkflowDataFlow';
import { ContextEngineeringSection } from '@/components/about/ContextEngineeringSection';
import { SmallModelsSection } from '@/components/about/SmallModelsSection';

export function AboutPage() {
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

        <InfoSection title="How the Pipeline Works">
          <SectionText>
            Each lesson flows through eight stages: from your lesson brief to a
            rendered video. Planning comes first, then code generation, an
            automated verify-and-fix loop, and finally an isolated render step.
          </SectionText>
          <WorkflowDataFlow />
        </InfoSection>

        <InfoSection title="Small Models, Big Results">
          <SectionText>
            MathAnimate routes each stage to a small, specialized model paired
            with curated context rather than throwing a single giant model at
            the whole problem. The result is faster, cheaper, and more reliable
            output.
          </SectionText>
          <div className="mt-6">
            <SmallModelsSection />
          </div>
        </InfoSection>

        <InfoSection title="What Goes Into Every Prompt">
          <SectionText>
            At each code stage the model receives a tightly scoped bundle:
            a stage-specific system prompt, the Manim skill reference, the
            Visual Kit API, and any scene templates that match the plan.
          </SectionText>
          <ContextEngineeringSection />
        </InfoSection>

        <InfoSection title="Open Source">
          <SectionText>
            MathAnimate is fully open source. Contributions, bug reports, and
            feature requests are welcome.
          </SectionText>
          <a
            href="https://github.com/Alonpenker/math-animate"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block text-accent-orange hover:underline"
          >
            View on GitHub →
          </a>
        </InfoSection>

      </div>
    </div>
  );
}
