const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export type JobStatus =
  | 'CREATED' | 'PLANNING' | 'PLANNED' | 'APPROVED'
  | 'CODEGEN' | 'CODED' | 'VERIFYING' | 'VERIFIED' | 'FIXING'
  | 'RENDERING' | 'RENDERED'
  | 'FAILED_PLANNING' | 'FAILED_CODEGEN' | 'FAILED_VERIFICATION' | 'FAILED_RENDER' | 'FAILED_QUOTA_EXCEEDED'
  | 'CANCELLED';

export interface Job {
  job_id: string;
  status: JobStatus;
}

export interface JobResponse {
  job: Job;
  data?: unknown;
}

export interface ScenePlan {
  scene_number: number;
  learning_objective: string;
  visual_storyboard: string;
  voice_notes: string;
  template_hints?: string;
}

export interface VideoPlan {
  scenes: ScenePlan[];
}

export interface PlanData {
  job_id: string;
  plan: VideoPlan;
  approved: boolean;
}

export interface UserRequest {
  topic: string;
  misconceptions: string[];
  constraints: string[];
  examples: string[];
  number_of_scenes: number;
}

export interface ArtifactResponse {
  artifact_id: string;
  job_id: string;
  artifact_type: string;
  name: string;
  size: number;
  sha256: string;
  created_at: string;
  updated_at: string;
}

export interface JobListItem {
  job_id: string;
  topic: string;
  status: JobStatus;
  number_of_scenes: number;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  jobs: JobListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface BreakdownEntry {
  provider: string;
  model: string;
  stage: string;
  consumed: number;
  reserved: number;
}

export interface TokenUsageResponse {
  day: string;
  daily_limit: number;
  soft_threshold: number;
  consumed: number;
  reserved: number;
  remaining: number;
  soft_threshold_exceeded: boolean;
  breakdown: BreakdownEntry[];
}

function createApiError(status: number, message: string): Error & { status: number } {
  const error = new Error(message) as Error & { status: number };
  error.name = 'ApiError';
  error.status = status;
  return error;
}

type ApiError = Error & { status: number };

function isApiError(err: unknown): err is ApiError {
  return err instanceof Error && 'status' in err && err.name === 'ApiError';
}

function isVideoPlan(data: unknown): data is VideoPlan {
  return (
    typeof data === 'object' &&
    data !== null &&
    'scenes' in data &&
    Array.isArray((data as { scenes?: unknown }).scenes)
  );
}

function isPlanData(data: unknown): data is PlanData {
  return (
    typeof data === 'object' &&
    data !== null &&
    'plan' in data &&
    isVideoPlan((data as { plan?: unknown }).plan)
  );
}

export function extractVideoPlan(data: unknown): VideoPlan | null {
  if (isVideoPlan(data)) {
    return data;
  }
  if (isPlanData(data)) {
    return data.plan;
  }
  return null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': import.meta.env.VITE_X_API_KEY ?? '',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw createApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}


export async function createJob(userRequest: UserRequest): Promise<JobResponse> {
  return request<JobResponse>('/jobs', {
    method: 'POST',
    body: JSON.stringify(userRequest),
  });
}

export async function getJobStatus(jobId: string): Promise<JobResponse> {
  return request<JobResponse>(`/jobs/${jobId}/status`);
}

export async function getJobPlan(jobId: string): Promise<JobResponse> {
  return request<JobResponse>(`/jobs/${jobId}/plan`);
}

export async function approveJob(jobId: string, approved: boolean): Promise<JobResponse> {
  return request<JobResponse>(`/jobs/${jobId}/approve?approved=${approved}`, {
    method: 'PATCH',
  });
}

export async function listJobs(params: {
  page?: number;
  page_size?: number;
  topic?: string;
  job_id?: string;
  status?: string;
}): Promise<JobListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page !== undefined) searchParams.set('page', String(params.page));
  if (params.page_size !== undefined) searchParams.set('page_size', String(params.page_size));
  if (params.topic) searchParams.set('topic', params.topic);
  if (params.job_id) searchParams.set('job_id', params.job_id);
  if (params.status) searchParams.set('status', params.status);
  return request<JobListResponse>(`/jobs?${searchParams.toString()}`);
}

export async function listArtifacts(params: {
  job_id?: string;
  artifact_type?: string;
}): Promise<ArtifactResponse[]> {
  const searchParams = new URLSearchParams();
  if (params.job_id) searchParams.set('job_id', params.job_id);
  if (params.artifact_type) searchParams.set('artifact_type', params.artifact_type);
  return request<ArtifactResponse[]>(`/artifacts?${searchParams.toString()}`);
}

export function getArtifactStreamUrl(artifactId: string): string {
  return `${BASE_URL}/artifacts/${artifactId}/stream`;
}


export async function getTokenUsage(): Promise<TokenUsageResponse> {
  return request<TokenUsageResponse>('/usage');
}

export { isApiError };
export type { ApiError };
