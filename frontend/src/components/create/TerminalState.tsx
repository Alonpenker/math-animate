import { useNavigate, Link } from 'react-router-dom';
import {
  CheckCircle2, AlertCircle, Code2, ShieldAlert, VideoOff, Gauge, XCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { JobStatus } from '@/services/api';

interface TerminalStateProps {
  status: JobStatus | null;
  jobId: string | null;
  onReset: () => void;
}

interface FailureInfo {
  icon: React.ReactNode;
  heading: string;
  explanation: string;
}

const FAILURE_MAP: Record<string, FailureInfo> = {
  FAILED_PLANNING: {
    icon: <AlertCircle className="h-16 w-16 text-red-500" />,
    heading: "Couldn't Generate a Plan",
    explanation: 'The AI was unable to create a plan for this topic. This can happen with very unusual or ambiguous topics. Try rephrasing the topic or loosening the constraints.',
  },
  FAILED_CODEGEN: {
    icon: <Code2 className="h-16 w-16 text-red-500" />,
    heading: 'Code Generation Failed',
    explanation: "The animation code couldn't be produced after multiple attempts. This sometimes happens with highly complex visual requirements. Simplifying the constraints may help.",
  },
  FAILED_VERIFICATION: {
    icon: <ShieldAlert className="h-16 w-16 text-red-500" />,
    heading: 'Code Verification Failed',
    explanation: "The generated code didn't pass our quality checks. The AI made its best attempt. Please try submitting again.",
  },
  FAILED_RENDER: {
    icon: <VideoOff className="h-16 w-16 text-red-500" />,
    heading: 'Rendering Failed',
    explanation: 'The rendering process encountered an unexpected error. Please try submitting your request again.',
  },
  FAILED_QUOTA_EXCEEDED: {
    icon: <Gauge className="h-16 w-16 text-orange-500" />,
    heading: 'Daily Token Limit Reached',
    explanation: 'The shared daily token budget has been exhausted. New jobs cannot be started until midnight UTC when the limit resets. Please try again later.',
  },
  CANCELLED: {
    icon: <XCircle className="h-16 w-16 text-orange-500" />,
    heading: 'Job Cancelled',
    explanation: 'This job was cancelled before it completed.',
  },
};

export function TerminalState({ status, jobId, onReset }: TerminalStateProps) {
  const navigate = useNavigate();

  if (status === 'RENDERED') {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <CheckCircle2 className="h-16 w-16 text-green-500" />
        <h2 className="mt-6 text-2xl font-bold text-brand-text">
          Your Lesson Videos Are Ready!
        </h2>
        <p className="mt-2 text-brand-muted">
          All scenes have been rendered successfully. Head to the Lessons library to watch them.
        </p>
        <Button
          onClick={() => navigate(`/lessons?job_id=${jobId}`)}
          className="mt-6 bg-brand-accent px-6 text-white hover:bg-brand-accent/90"
          size="lg"
        >
          Watch My Videos &rarr;
        </Button>
      </div>
    );
  }

  const info = status ? FAILURE_MAP[status] : null;
  if (!info) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <AlertCircle className="h-16 w-16 text-brand-muted" />
        <h2 className="mt-6 text-2xl font-bold text-brand-text">Unknown Status</h2>
        <p className="mt-2 text-brand-muted">Something unexpected happened.</p>
        <Button onClick={onReset} className="mt-6" variant="outline">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center py-16 text-center">
      {info.icon}
      <h2 className="mt-6 text-2xl font-bold text-brand-text">{info.heading}</h2>
      <p className="mx-auto mt-2 max-w-md text-brand-muted">{info.explanation}</p>
      <Link
        to="/create"
        className="mt-6 inline-flex items-center justify-center rounded-lg bg-brand-accent px-6 h-9 text-base font-semibold text-white hover:bg-brand-accent/90 no-underline"
      >
        Try Again
      </Link>
    </div>
  );
}
