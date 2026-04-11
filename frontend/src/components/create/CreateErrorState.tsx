import { Link } from 'react-router-dom';
import { buttonVariants } from '@/components/ui/button';

interface CreateErrorStateProps {
  title: string;
  error: string | null;
  onStartFresh: () => void;
}

export function CreateErrorState({ title, error, onStartFresh }: CreateErrorStateProps) {
  return (
    <div className="flex items-center justify-center px-4 py-12">
      <div className="text-center">
        <h1 className="text-2xl text-off-white">
          {title}
        </h1>
        {error && <p className="mt-2 text-off-white/50">{error}</p>}
        <Link
          to="/create"
          onClick={onStartFresh}
          className={buttonVariants({ variant: 'outline' }) + ' mt-6 border-accent-orange text-accent-orange hover:bg-accent-orange/10 no-underline'}
        >
          Start Fresh
        </Link>
      </div>
    </div>
  );
}
