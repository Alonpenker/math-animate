import { useState } from 'react';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import type { VideoPlan } from '@/services/api';

interface PlanReviewProps {
  plan: VideoPlan;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
  error: string | null;
}

export function PlanReview({ plan, onApprove, onReject, error }: PlanReviewProps) {
  const [loading, setLoading] = useState(false);
  const scenes = Array.isArray(plan.scenes) ? plan.scenes : [];

  const handleApprove = async () => { setLoading(true); try { await onApprove(); } finally { setLoading(false); } };
  const handleReject = async () => { setLoading(true); try { await onReject(); } finally { setLoading(false); } };

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-3xl text-off-white">
        Your Lesson Plan is Ready — Review it below
      </h2>
      <p className="mt-2 text-off-white/60">
        If the plan looks good, approve it and we'll start generating the animations.
      </p>

      <div className="mt-8 space-y-5">
        {scenes.length === 0 && (
          <div
            className="rounded-md p-6 text-sm text-off-white/60"
            style={{ border: '1px solid rgba(245,240,232,0.2)', background: 'rgba(245,240,232,0.04)' }}
          >
            Plan data is unavailable. Please refresh and try again.
          </div>
        )}
        {scenes.map((scene) => (
          <div
            key={scene.scene_number}
            className="rounded-md p-5"
            style={{ border: '1px solid rgba(245,240,232,0.16)', background: 'rgba(245,240,232,0.04)' }}
          >
            <h3 className="mb-4 text-lg text-off-white">
              Scene {scene.scene_number}
            </h3>
            <div className="space-y-4">
              {[
                { label: 'Learning Objective', value: scene.learning_objective },
                { label: 'Visual Storyboard', value: scene.visual_storyboard },
                { label: 'Voice Notes', value: scene.voice_notes },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs font-semibold uppercase tracking-wide text-off-white/45">{label}</p>
                  <p className="mt-1 text-sm text-off-white/80">{value}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div
          className="mt-4 rounded-md p-3 text-sm text-red-700"
          style={{ background: 'rgba(220,38,38,0.08)', border: '1px solid rgba(220,38,38,0.3)' }}
        >
          {error}
        </div>
      )}

      <div className="mt-8 flex items-center gap-4">
        <Button
          onClick={handleApprove}
          disabled={loading}
          variant="default"
          size="lg"
          className="h-10 min-w-33 bg-accent-orange px-6 text-base hover:brightness-110"
        >
          {loading ? 'Processing...' : 'Approve'}
        </Button>

        <AlertDialog>
          <AlertDialogTrigger
            disabled={loading}
            className="inline-flex h-10 min-w-33 cursor-pointer items-center justify-center rounded-lg border-2 border-red-600 bg-transparent px-6 text-base text-red-600 transition-all hover:bg-red-600 hover:text-white disabled:opacity-40"
          >
            Reject
          </AlertDialogTrigger>
          <AlertDialogContent style={{ background: '#1e2b2e', border: '2px solid rgba(245,240,232,0.2)' }}>
            <AlertDialogHeader>
              <AlertDialogTitle className="text-off-white">Reject this plan?</AlertDialogTitle>
              <AlertDialogDescription className="text-off-white/60">
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
