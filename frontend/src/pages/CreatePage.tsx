import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { CreateForm } from '@/components/create/CreateForm';
import { DynamicLoader } from '@/components/create/DynamicLoader';
import { PlanReview } from '@/components/create/PlanReview';
import { TerminalState } from '@/components/create/TerminalState';
import { useCreateFlow } from '@/hooks/useCreateFlow';

export function CreatePage() {
  const {
    state,
    pollingStatus,
    pollingError,
    submit,
    approvePlan,
    rejectPlan,
    resetToForm,
  } = useCreateFlow();

  // Not found
  if (state.phase === 'not_found') {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-brand-text">Job Not Found</h1>
        <p className="mt-2 text-brand-muted">{state.error}</p>
        <Link
          to="/create"
          className="mt-6 inline-flex items-center justify-center rounded-lg bg-brand-accent px-4 h-8 text-sm font-medium text-white hover:bg-brand-accent/90 no-underline"
        >
          Start Fresh
        </Link>
      </div>
    );
  }

  // Resume error
  if (state.phase === 'resume_error') {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-brand-text">Connection Error</h1>
        <p className="mt-2 text-brand-muted">{state.error}</p>
        <Button
          onClick={() => window.location.reload()}
          variant="outline"
          className="mt-6"
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      {state.phase === 'form' && (
        <>
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-brand-text">Create a Lesson Video</h1>
            <p className="mt-2 text-brand-muted">
              Fill in the brief below and our AI will plan and render your lesson.
            </p>
          </div>
          <CreateForm onSubmit={submit} error={state.error} />
        </>
      )}

      {state.phase === 'loading_planning' && (
        <DynamicLoader status={pollingStatus} connectionError={pollingError} />
      )}

      {state.phase === 'plan_review' && state.plan && (
        <PlanReview
          plan={state.plan}
          onApprove={approvePlan}
          onReject={rejectPlan}
          error={state.error}
        />
      )}

      {state.phase === 'plan_review' && !state.plan && state.error && (
        <div className="py-16 text-center">
          <p className="text-brand-muted">{state.error}</p>
        </div>
      )}

      {state.phase === 'loading_rendering' && (
        <DynamicLoader status={pollingStatus} connectionError={pollingError} />
      )}

      {state.phase === 'rejected' && (
        <div className="flex flex-col items-center py-16 text-center">
          <h2 className="text-2xl font-bold text-brand-text">No problem.</h2>
          <p className="mt-2 text-brand-muted">
            Your plan has been cancelled. Ready to try a different approach? Head back to the form.
          </p>
          <Button
            onClick={resetToForm}
            className="mt-6 bg-brand-accent px-6 text-white hover:bg-brand-accent/90"
            size="lg"
          >
            Create a New Lesson
          </Button>
        </div>
      )}

      {(state.phase === 'success' || state.phase === 'failure' || state.phase === 'cancelled') && (
        <TerminalState
          status={
            state.phase === 'success'
              ? 'RENDERED'
              : state.phase === 'cancelled'
              ? 'CANCELLED'
              : state.failureStatus
          }
          jobId={state.jobId}
          onReset={resetToForm}
        />
      )}
    </div>
  );
}
