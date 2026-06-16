import { HeroSection } from '@/components/home/HeroSection';
import { TechLoopStrip } from '@/components/home/TechLoopStrip';
import { ShowcaseReelSection } from '@/components/home/ShowcaseReelSection';
import { HowItWorksSection } from '@/components/home/HowItWorksSection';
import { AboutSection } from '@/components/home/AboutSection';

export function HomePage() {
  return (
    <>
      <HeroSection />
      <TechLoopStrip />
      <ShowcaseReelSection />
      <HowItWorksSection />
      <AboutSection />
    </>
  );
}
