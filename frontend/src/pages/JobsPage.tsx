import { useState } from 'react';
import { motion } from 'framer-motion';
import { TooltipProvider } from '@/components/ui/tooltip';
import { JobsTable } from '@/components/jobs/JobsTable';
import { useJobsList } from '@/hooks/useJobsList';

const PAGE_SIZE = 20;

export function JobsPage() {
  const [page, setPage] = useState(1);
  const { jobs, total, loading, error, refetch } = useJobsList({ page, page_size: PAGE_SIZE });

  return (
    <div className="px-4 py-12">
      <motion.div
        className="mx-auto max-w-5xl"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-8">
          <h1
            className="text-4xl text-chalk-white"
            style={{ fontFamily: 'Patrick Hand, cursive' }}
          >
            Job History
          </h1>
          <p className="mt-2 text-chalk-white/50" style={{ fontFamily: 'Inter, sans-serif' }}>
            All lesson generation jobs.
          </p>
        </div>
        <TooltipProvider>
          <JobsTable
            jobs={jobs}
            total={total}
            page={page}
            pageSize={PAGE_SIZE}
            loading={loading}
            error={error}
            onPageChange={setPage}
            onRetry={refetch}
          />
        </TooltipProvider>
      </motion.div>
    </div>
  );
}
