import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Search, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { LessonCard } from '@/components/lessons/LessonCard';
import { LessonDialog } from '@/components/lessons/LessonDialog';
import { useLessons } from '@/hooks/useLessons';
import type { JobListItem } from '@/services/api';

const PAGE_SIZE = 20;

export function LessonsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const jobIdFilter = searchParams.get('job_id') ?? undefined;

  const [topicQuery, setTopicQuery] = useState('');
  const [page, setPage] = useState(1);
  const [selectedJob, setSelectedJob] = useState<JobListItem | null>(null);

  const { jobs, total, loading, error } = useLessons({
    topicQuery,
    jobId: jobIdFilter,
    page,
  });

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-brand-text">Lesson Library</h1>
        <p className="mt-2 text-brand-muted">Browse and watch your rendered lesson videos.</p>
      </div>

      {/* Search bar */}
      <div className="relative mb-8">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-muted" />
        <input
          type="text"
          value={topicQuery}
          onChange={(e) => {
            setTopicQuery(e.target.value);
            setPage(1);
          }}
          placeholder="Search by topic..."
          className="w-full rounded-md border border-brand-border py-2 pl-10 pr-4 text-sm text-brand-text outline-none focus:border-brand-light focus:ring-1 focus:ring-brand-light"
        />
      </div>

      {error && (
        <div className="flex flex-col items-center py-16 text-center">
          <p className="text-brand-muted">Could not load lessons.</p>
          <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      )}

      {loading && !error && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-[140px] rounded-lg" />
          ))}
        </div>
      )}

      {!loading && !error && jobs.length === 0 && (
        <div className="flex flex-col items-center py-16 text-center">
          <BookOpen className="h-12 w-12 text-brand-muted" />
          <p className="mt-4 text-brand-muted">No rendered videos yet. Create your first lesson!</p>
          <Button
            onClick={() => navigate('/create')}
            className="mt-4 bg-brand-accent text-white hover:bg-brand-accent/90"
          >
            Create a Lesson
          </Button>
        </div>
      )}

      {!loading && !error && jobs.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <LessonCard
                key={job.job_id}
                job={job}
                onClick={() => setSelectedJob(job)}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-4">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-brand-muted">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}

      {selectedJob && (
        <LessonDialog
          open={!!selectedJob}
          onOpenChange={(open) => { if (!open) setSelectedJob(null); }}
          jobId={selectedJob.job_id}
          topic={selectedJob.topic}
        />
      )}
    </div>
  );
}
