import LogoLoop from '@/components/ui/LogoLoop';
import { LOGOS } from '@/components/home/LogoIcon';


export function TechLoopStrip() {
  return (
    <div className="py-8 border-y border-off-white/10">
      <p className="text-center text-xs text-off-white/30 mb-6">Built with</p>
        <LogoLoop
          logos={LOGOS}
          speed={60}
          direction="left"
          logoHeight={48}
          gap={56}
          pauseOnHover
          scaleOnHover={true}
          fadeOut
          fadeOutColor="#000000"
          ariaLabel="Technologies used"
        />
    </div>
  );
}
