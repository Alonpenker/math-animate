import { motion } from 'framer-motion';
import { CreateErrorState } from '@/components/create/CreateErrorState';
import { CreateForm } from '@/components/create/CreateForm';
import { DynamicLoader } from '@/components/create/DynamicLoader';
import { PlanReview } from '@/components/create/PlanReview';
import { TerminalState } from '@/components/create/TerminalState';
import { JobStateDiagram } from '@/components/create/JobStateDiagram';
import { useCreateFlow } from '@/hooks/create/useCreateFlow';
import {
  isFailureState,
  isPlanningState,
  isRenderingState,
  isTerminalState,
} from '@/hooks/create/createFlowState';

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
  const liveBackendState =
    isPlanningState(state.currentState) || isRenderingState(state.currentState)
      ? state.currentState
      : null;
  const isLiveState = liveBackendState !== null || pollingStatus === 'TIMEOUT';
  let content;

  if (state.currentState === 'NOT_FOUND') {
    content = (<CreateErrorState title="Job Not Found" error={state.error} onStartFresh={resetToForm} />);
  }

  if (state.currentState === 'RESUME_ERROR') {
    content = (<CreateErrorState title="Connection Error" error={state.error} onStartFresh={resetToForm} />);
  }

  if (state.currentState === 'FORM') {
    content = (<>
      <div className="mb-8 text-center">
        <h1 className="text-4xl text-off-white">
          Create a Lesson Video
        </h1>
        <p className="mt-2 text-off-white/60">
          Fill in the brief below and our AI will plan and render your lesson.
        </p>
      </div>
      <CreateForm onSubmit={submit} error={state.error} />
    </>);
  }

  if (isLiveState) {
    content = (<>
      <DynamicLoader
        status={pollingStatus === 'TIMEOUT' ? 'TIMEOUT' : liveBackendState}
        connectionError={pollingError}
      />
      <JobStateDiagram currentStatus={liveBackendState} mode="live" />
    </>);
  }

  if (state.currentState === 'PLANNED' && state.plan) {
    content = (<div
      className="rounded-xl py-10 px-10 shadow-lg"
      style={{ border: '1px solid rgba(245,240,232,0.15)', background: 'rgba(245,240,232,0.05)' }}
    >
      <PlanReview plan={state.plan} onApprove={approvePlan} onReject={rejectPlan} error={state.error} />
    </div>);
  }

  if (isTerminalState(state.currentState)) {
    content = (<TerminalState
      status={
        state.currentState === 'RENDERED'
          ? 'RENDERED'
          : state.currentState === 'CANCELLED'
            ? 'CANCELLED'
            : isFailureState(state.currentState)
              ? state.currentState
              : null
      }
      jobId={state.jobId}
      onReset={resetToForm}
    />);
  }

  if (!content && state.error) {
    content = <CreateErrorState title="Something Went Wrong" error={state.error} onStartFresh={resetToForm} />;
  }

  return (
    <div className="px-4 py-12">
      <motion.div
        className="mx-auto max-w-4xl"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}>
      {content}
      </motion.div>
    </div>
  );
}
