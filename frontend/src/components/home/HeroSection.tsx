import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="bg-brand px-4 py-20 md:py-28">
      <div className="mx-auto max-w-3xl text-center">
        <h1 className="text-3xl font-bold leading-tight text-white md:text-5xl">
          Turn Lesson Ideas into Animated Math Videos
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-base text-white/70 md:text-lg">
          Describe your topic. Let AI plan and render the lesson. Watch it come to life in minutes.
        </p>
        <Button
          onClick={() => navigate('/create')}
          className="mt-8 bg-brand-accent px-6 py-3 text-base font-semibold text-white hover:bg-brand-accent/90"
          size="lg"
        >
          Try It Now &rarr;
        </Button>
      </div>
    </section>
  );
}
