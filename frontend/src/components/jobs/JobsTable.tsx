import { useNavigate } from 'react-router-dom';
import { Inbox } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Tooltip, TooltipContent, TooltipTrigger,
} from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge';
import { formatDate, truncateId } from '@/utils/formatters';
import type { JobListItem, JobStatus } from '@/services/api';

interface JobsTableProps {
  jobs: JobListItem[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: Error | null;
  onPageChange: (page: number) => void;
  onRetry: () => void;
}

function isClickable(status: JobStatus): boolean {
  return status === 'PLANNED' || status === 'RENDERED';
}

function getClickRoute(job: JobListItem): string | null {
  if (job.status === 'PLANNED') return `/create?job_id=${job.job_id}`;
  if (job.status === 'RENDERED') return `/lessons?job_id=${job.job_id}`;
  return null;
}

const cellStyle: React.CSSProperties = {
  padding: '12px 16px',
  borderBottom: '1px solid rgba(245,240,232,0.1)',
  fontSize: '14px',
  color: '#F5F0E8',
};

const headerCellStyle: React.CSSProperties = {
  ...cellStyle,
  color: 'rgba(245,240,232,0.45)',
  fontSize: '11px',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  borderBottom: '1px solid rgba(245,240,232,0.2)',
};

export function JobsTable({ jobs, total, page, pageSize, loading, error, onPageChange, onRetry }: JobsTableProps) {
  const navigate = useNavigate();
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (error) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-off-white/50">Could not load jobs.</p>
        <Button variant="outline" className="mt-4" onClick={onRetry}>Retry</Button>
      </div>
    );
  }

  if (!loading && jobs.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <Inbox className="h-12 w-12 text-off-white/30" />
        <p className="mt-4 text-off-white/50">No jobs yet. Go create the first lesson video!</p>
        <Button className="mt-4 bg-accent-orange hover:bg-accent-orange/80" onClick={() => navigate('/create')}>
          Create a Lesson
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div
        className="overflow-x-auto rounded-lg"
        style={{ border: '1px solid rgba(245,240,232,0.2)', background: 'rgba(0,0,0,0.25)' }}
      >
        <table className="w-full text-left" style={{ borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={headerCellStyle}>Job ID</th>
              <th style={headerCellStyle}>Topic</th>
              <th style={headerCellStyle}>Status</th>
              <th style={headerCellStyle}>Created</th>
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <tr key={i}>
                    {[40, 160, 112, 128].map((w, j) => (
                      <td key={j} style={cellStyle}>
                        <Skeleton className="h-4 rounded-sm" style={{ width: w, background: 'rgba(245,240,232,0.1)' }} />
                      </td>
                    ))}
                  </tr>
                ))
              : jobs.map((job) => {
                  const clickable = isClickable(job.status);
                  const route = getClickRoute(job);
                  return (
                    <tr
                      key={job.job_id}
                      onClick={route ? () => navigate(route) : undefined}
                      style={{ cursor: clickable ? 'pointer' : 'default' }}
                      className={clickable ? 'hover:bg-white/5 transition-colors' : ''}
                    >
                      <td style={{ ...cellStyle, fontFamily: 'monospace', fontSize: '12px', color: 'rgba(245,240,232,0.5)' }}>
                        <Tooltip>
                          <TooltipTrigger className="cursor-default">
                            {truncateId(job.job_id)}
                          </TooltipTrigger>
                          <TooltipContent>{job.job_id}</TooltipContent>
                        </Tooltip>
                      </td>
                      <td style={cellStyle}>{job.topic}</td>
                      <td style={cellStyle}><JobStatusBadge status={job.status} /></td>
                      <td style={{ ...cellStyle, color: 'rgba(245,240,232,0.45)' }}>{formatDate(job.created_at)}</td>
                    </tr>
                  );
                })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-5 flex items-center justify-center gap-5">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
            Previous
          </Button>
          <span className="text-sm text-off-white/50">
            Page {page} of {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
