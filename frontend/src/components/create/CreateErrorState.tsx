import { Link } from 'react-router-dom';

interface CreateErrorStateProps {
  title: string;
  error: string | null;
  onStartFresh: () => void;
}

export function CreateErrorState({ title, error, onStartFresh }: CreateErrorStateProps) {
  return (
    <div className="flex items-center justify-center px-4 py-12">
      <div className="text-center">
        <h1 className="text-2xl text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>
          {title}
        </h1>
        {error && <p className="mt-2 text-chalk-white/50">{error}</p>}
        <Link
          to="/create"
          onClick={onStartFresh}
          className="mt-6 inline-flex items-center justify-center rounded-lg border-2 border-chalk-orange px-4 py-2 text-sm text-chalk-orange no-underline hover:bg-chalk-orange/10"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Start Fresh
        </Link>
      </div>
    </div>
  );
}
