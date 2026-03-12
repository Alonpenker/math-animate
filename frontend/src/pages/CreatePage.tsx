import { motion } from 'framer-motion';
import { CreateErrorState } from '@/components/create/CreateErrorState';
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

  if (state.phase === 'not_found') {
    return <CreateErrorState title="Job Not Found" error={state.error} onStartFresh={resetToForm} />;
  }

  if (state.phase === 'resume_error') {
    return <CreateErrorState title="Connection Error" error={state.error} onStartFresh={resetToForm} />;
  }

  return (
    <div className="px-4 py-12">
      <motion.div
        className="mx-auto max-w-4xl"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {state.phase === 'form' && (
          <>
            <div className="mb-8 text-center">
              <h1 className="text-4xl text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>
                Create a Lesson Video
              </h1>
              <p className="mt-2 text-chalk-white/60" style={{ fontFamily: 'Inter, sans-serif' }}>
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
          <div
            className="rounded-xl py-10 px-10 shadow-lg"
            style={{ border: '1px solid rgba(245,240,232,0.15)', background: 'rgba(245,240,232,0.05)' }}
          >
            <PlanReview plan={state.plan} onApprove={approvePlan} onReject={rejectPlan} error={state.error} />
          </div>
        )}

        {state.phase === 'plan_review' && !state.plan && state.error && (
          <div className="py-16 text-center">
            <p className="text-chalk-white/60">{state.error}</p>
          </div>
        )}

        {state.phase === 'loading_rendering' && (
          <DynamicLoader status={pollingStatus} connectionError={pollingError} />
        )}

        {state.phase === 'rejected' && (
          <div className="flex flex-col items-center py-16 text-center">
            <h2 className="text-2xl text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>No problem.</h2>
            <p className="mt-2 text-chalk-white/60" style={{ fontFamily: 'Inter, sans-serif' }}>
              Your plan has been cancelled. Ready to try a different approach? Head back to the form.
            </p>
            <motion.button
              onClick={resetToForm}
              className="mt-6 rounded-lg border-2 border-chalk-orange px-8 py-3 text-lg text-chalk-orange hover:bg-chalk-orange hover:text-white transition-all cursor-pointer"
              style={{ fontFamily: 'Patrick Hand, cursive', background: 'none' }}
              whileHover={{ scale: 1.03 }}
            >
              Create a New Lesson
            </motion.button>
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
      </motion.div>
    </div>
  );
}
