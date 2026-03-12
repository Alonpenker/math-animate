import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CheckCircle2, AlertCircle, Code2, ShieldAlert, VideoOff, Gauge, XCircle,
} from 'lucide-react';
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
    icon: <Gauge className="h-16 w-16 text-chalk-orange" />,
    heading: 'Daily Token Limit Reached',
    explanation: 'The shared daily token budget has been exhausted. Please try again after midnight UTC.',
  },
  CANCELLED: {
    icon: <XCircle className="h-16 w-16 text-chalk-orange" />,
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
        <CheckCircle2 className="h-16 w-16 text-chalk-green" />
        <h2 className="mt-6 text-3xl text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>
          Your Lesson Videos Are Ready!
        </h2>
        <p className="mt-2 text-chalk-white/55 max-w-md" style={{ fontFamily: 'Inter, sans-serif' }}>
          All scenes have been rendered successfully. Head to the Lessons library to watch them.
        </p>
        <button
          onClick={() => navigate(`/lessons?job_id=${jobId}`)}
          className="mt-8 rounded-lg border-2 border-chalk-orange text-chalk-orange px-8 py-3 text-lg transition-all hover:bg-chalk-orange hover:text-white cursor-pointer"
          style={{ fontFamily: 'Patrick Hand, cursive', background: 'none' }}
        >
          Watch My Videos →
        </button>
      </motion.div>
    );
  }

  const info = status ? FAILURE_MAP[status] : null;
  if (!info) {
    return (
      <div className="flex flex-col items-center py-20 text-center">
        <AlertCircle className="h-16 w-16 text-chalk-white/30" />
        <h2 className="mt-6 text-2xl text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>Unknown Status</h2>
        <button onClick={onReset} className="mt-6 rounded-lg border-2 border-chalk-white/40 text-chalk-white/70 px-5 py-2 hover:bg-white/5 cursor-pointer" style={{ fontFamily: 'Inter, sans-serif', background: 'none' }}>
          Try Again
        </button>
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
      <h2 className="mt-6 text-3xl text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>
        {info.heading}
      </h2>
      <p className="mx-auto mt-2 max-w-md text-chalk-white/55" style={{ fontFamily: 'Inter, sans-serif' }}>
        {info.explanation}
      </p>
      <button
        onClick={onReset}
        className="mt-8 rounded-lg border-2 border-chalk-orange text-chalk-orange px-8 py-3 text-lg transition-all hover:bg-chalk-orange hover:text-white cursor-pointer"
        style={{ fontFamily: 'Patrick Hand, cursive', background: 'none' }}
      >
        Try Again
      </button>
    </motion.div>
  );
}
