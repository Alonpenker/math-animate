import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import type { VideoPlan } from '@/services/api';

interface PlanReviewProps {
  plan: VideoPlan;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
  error: string | null;
}

export function PlanReview({ plan, onApprove, onReject, error }: PlanReviewProps) {
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    setLoading(true);
    try {
      await onApprove();
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    setLoading(true);
    try {
      await onReject();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-2xl font-bold text-brand-text">
        Your Lesson Plan is Ready — Review it below
      </h2>
      <p className="mt-2 text-brand-muted">
        If the plan looks good, approve it and we'll start generating the animations.
      </p>

      <div className="mt-8 space-y-6">
        {plan.scenes.map((scene) => (
          <div
            key={scene.scene_number}
            className="rounded-lg border border-brand-border p-6"
          >
            <h3 className="mb-4 text-lg font-semibold text-brand">
              Scene {scene.scene_number}
            </h3>
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-muted">
                  Learning Objective
                </p>
                <p className="mt-1 text-sm text-brand-text">{scene.learning_objective}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-muted">
                  Visual Storyboard
                </p>
                <p className="mt-1 text-sm text-brand-text">{scene.visual_storyboard}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-muted">
                  Voice Notes
                </p>
                <p className="mt-1 text-sm text-brand-text">{scene.voice_notes}</p>
              </div>
              {scene.template_hints && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand-muted">
                    Template Hints
                  </p>
                  <p className="mt-1 text-xs text-brand-muted italic">{scene.template_hints}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mt-8 flex items-center gap-4">
        <Button
          onClick={handleApprove}
          disabled={loading}
          className="bg-brand px-6 text-white hover:bg-brand/90"
        >
          {loading ? 'Processing...' : 'Approve'}
        </Button>

        <AlertDialog>
          <AlertDialogTrigger
            disabled={loading}
            className="inline-flex shrink-0 items-center justify-center rounded-lg border border-red-300 bg-background px-2.5 h-8 text-sm font-medium text-red-600 hover:bg-red-50 disabled:pointer-events-none disabled:opacity-50"
          >
            Reject
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Reject this plan?</AlertDialogTitle>
              <AlertDialogDescription>
                This will cancel the job permanently. You'll need to create a new request.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Go Back</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleReject}
                className="bg-red-600 text-white hover:bg-red-700"
              >
                Yes, Reject
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}
