import { HeroSection } from '@/components/home/HeroSection';
import { TechLoopStrip } from '@/components/home/TechLoopStrip';
import { HowItWorksSection } from '@/components/home/HowItWorksSection';
import { AboutSection } from '@/components/home/AboutSection';

export function HomePage() {
  return (
    <>
      <HeroSection />
      <TechLoopStrip />
      <HowItWorksSection />
      <AboutSection />
    </>
  );
}
