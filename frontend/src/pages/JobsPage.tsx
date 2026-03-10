import { useState } from 'react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { JobsTable } from '@/components/jobs/JobsTable';
import { useJobsList } from '@/hooks/useJobsList';

const PAGE_SIZE = 20;

export function JobsPage() {
  const [page, setPage] = useState(1);

  const { jobs, total, loading, error, refetch } = useJobsList({
    page,
    page_size: PAGE_SIZE,
  });

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-brand-text">Job History</h1>
        <p className="mt-2 text-brand-muted">All lesson generation jobs.</p>
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
    </div>
  );
}
