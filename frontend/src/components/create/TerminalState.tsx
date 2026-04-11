import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
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

const FAILURE_MAP: Record<string, { icon: React.ReactNode; heading: string; explanation: string }> = {
  FAILED_PLANNING: {
    icon: <AlertCircle className="h-16 w-16 text-red-400" />,
    heading: "Couldn't Generate a Plan",
    explanation: 'The AI was unable to create a plan for this topic. Try rephrasing the topic or loosening the constraints.',
  },
  FAILED_CODEGEN: {
    icon: <Code2 className="h-16 w-16 text-red-400" />,
    heading: 'Code Generation Failed',
    explanation: "The animation code couldn't be produced after multiple attempts. Simplifying the constraints may help.",
  },
  FAILED_VERIFICATION: {
    icon: <ShieldAlert className="h-16 w-16 text-red-400" />,
    heading: 'Code Verification Failed',
    explanation: "The generated code didn't pass our quality checks. Please try submitting again.",
  },
  FAILED_RENDER: {
    icon: <VideoOff className="h-16 w-16 text-red-400" />,
    heading: 'Rendering Failed',
    explanation: 'The rendering process encountered an unexpected error. Please try submitting your request again.',
  },
  FAILED_QUOTA_EXCEEDED: {
    icon: <Gauge className="h-16 w-16 text-accent-orange" />,
    heading: 'Daily Token Limit Reached',
    explanation: 'The shared daily token budget has been exhausted. Please try again after midnight UTC.',
  },
  CANCELLED: {
    icon: <XCircle className="h-16 w-16 text-accent-orange" />,
    heading: 'Job Cancelled',
    explanation: 'This job was cancelled before it completed.',
  },
};

export function TerminalState({ status, jobId, onReset }: TerminalStateProps) {
  const navigate = useNavigate();

  if (status === 'RENDERED') {
    return (
      <motion.div
        className="flex flex-col items-center py-20 text-center"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <CheckCircle2 className="h-16 w-16 text-accent-green" />
        <h2 className="mt-6 text-3xl text-off-white">
          Your Lesson Videos Are Ready!
        </h2>
        <p className="mt-2 text-off-white/55 max-w-md">
          All scenes have been rendered successfully. Head to the Lessons library to watch them.
        </p>
        <Button
          onClick={() => navigate(`/lessons?job_id=${jobId}`)}
          size="lg"
          className="mt-8 bg-accent-orange hover:bg-accent-orange/80"
        >
          Watch My Videos →
        </Button>
      </motion.div>
    );
  }

  const info = status ? FAILURE_MAP[status] : null;
  if (!info) {
    return (
      <div className="flex flex-col items-center py-20 text-center">
        <AlertCircle className="h-16 w-16 text-off-white/30" />
        <h2 className="mt-6 text-2xl text-off-white">Unknown Status</h2>
        <Button variant="outline" onClick={onReset} className="mt-6">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <motion.div
      className="flex flex-col items-center py-20 text-center"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      {info.icon}
      <h2 className="mt-6 text-3xl text-off-white">
        {info.heading}
      </h2>
      <p className="mx-auto mt-2 max-w-md text-off-white/55">
        {info.explanation}
      </p>
      <Button
        onClick={onReset}
        size="lg"
        className="mt-8 bg-accent-orange hover:bg-accent-orange/80"
      >
        Try Again
      </Button>
    </motion.div>
  );
}
