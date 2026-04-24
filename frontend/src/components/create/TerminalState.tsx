import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CheckCircle2, AlertCircle, Code2, ShieldAlert, VideoOff, Gauge, XCircle,
  BrainCircuit,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { JOB_STATUS_DEFS } from '@/domain/jobStatus';
import type { JobStatus } from '@/services/api';

interface TerminalStateProps {
  status: JobStatus | null;
  jobId: string | null;
  onReset: () => void;
}

const ICON_MAP: Record<string, LucideIcon> = {
  AlertCircle,
  BrainCircuit,
  Code2,
  Gauge,
  ShieldAlert,
  VideoOff,
  XCircle,
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

  const statusDef = status ? JOB_STATUS_DEFS[status] : null;
  const info = statusDef?.terminal;
  if (!info) {
    return (
      <div className="flex flex-col items-center py-20 text-center">
        <AlertCircle className="h-16 w-16 text-off-white/30" />
        <h2 className="mt-6 text-2xl text-off-white">Unknown Terminal Status</h2>
        <p className="mx-auto mt-2 max-w-md text-off-white/55">
          This job reached a state the interface does not recognize. Please try again.
        </p>
        <Button variant="outline" onClick={onReset} className="mt-6">
          Try Again
        </Button>
      </div>
    );
  }

  const Icon = ICON_MAP[info.icon] ?? AlertCircle;
  const iconColorClass = statusDef?.color === 'orange' || statusDef?.kind === 'cancelled'
    ? 'text-accent-orange'
    : 'text-red-400';

  return (
    <motion.div
      className="flex flex-col items-center py-20 text-center"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Icon className={`h-16 w-16 ${iconColorClass}`} />
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
