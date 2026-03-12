import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Search, BookOpen } from 'lucide-react';
import { motion } from 'framer-motion';
import { Skeleton } from '@/components/ui/skeleton';
import { ChalkButton } from '@/components/chalk/ChalkButton';
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
  const { jobs, total, loading, error } = useLessons({ topicQuery, jobId: jobIdFilter, page });
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="px-4 py-12">
      <motion.div
        className="mx-auto max-w-5xl"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-8">
          <h1 className="text-4xl text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>
            Lesson Library
          </h1>
          <p className="mt-2 text-chalk-white/50" style={{ fontFamily: 'Inter, sans-serif' }}>
            Browse and watch your rendered lesson videos.
          </p>
        </div>

        <div className="relative mb-8">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-chalk-white/40" />
          <input
            type="text"
            value={topicQuery}
            onChange={(e) => { setTopicQuery(e.target.value); setPage(1); }}
            placeholder="Search by topic..."
            className="chalk-input-dark"
            style={{ fontFamily: 'Inter, sans-serif', paddingLeft: '2.5rem' }}
          />
        </div>

        {error && (
          <div className="flex flex-col items-center py-16 text-center">
            <p className="text-chalk-white/50">Could not load lessons.</p>
            <ChalkButton variant="default" className="mt-4" onClick={() => window.location.reload()}>Retry</ChalkButton>
          </div>
        )}

        {loading && !error && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-36 rounded-[10px]" style={{ background: 'rgba(245,240,232,0.08)' }} />
            ))}
          </div>
        )}

        {!loading && !error && jobs.length === 0 && (
          <div className="flex flex-col items-center py-16 text-center">
            <BookOpen className="h-12 w-12 text-chalk-white/30" />
            <p className="mt-4 text-chalk-white/50">No rendered videos yet. Create your first lesson!</p>
            <ChalkButton variant="orange" className="mt-4" onClick={() => navigate('/create')}>
              Create a Lesson
            </ChalkButton>
          </div>
        )}

        {!loading && !error && jobs.length > 0 && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {jobs.map((job) => (
                <LessonCard key={job.job_id} job={job} onClick={() => setSelectedJob(job)} />
              ))}
            </div>
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-5">
                <ChalkButton variant="default" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</ChalkButton>
                <span className="text-sm text-chalk-white/50">Page {page} of {totalPages}</span>
                <ChalkButton variant="default" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</ChalkButton>
              </div>
            )}
          </>
        )}
      </motion.div>

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
