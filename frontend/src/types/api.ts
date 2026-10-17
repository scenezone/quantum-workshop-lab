export type ExperimentId = 'superposition' | 'bell_entanglement' | 'interference';

export interface Experiment {
  experiment_id: ExperimentId;
  title: string;
  description: string;
  qubits: number;
  ideal_probabilities: Record<string, number>;
}

export interface ExperimentResult {
  experiment_id: string;
  backend: 'aer_simulator' | 'ibm_quantum';
  backend_name: string | null;
  shots: number;
  counts: Record<string, number>;
  observed_probabilities: Record<string, number>;
  ideal_probabilities: Record<string, number>;
  provider_job_id: string | null;
  tracking_id: string | null;
}

export type JobStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'unknown';

export interface JobStatusResponse {
  tracking_id: string;
  status: JobStatus;
  experiment_id: string;
  backend_name: string | null;
  provider_job_id: string | null;
  shots: number;
  counts: Record<string, number> | null;
  observed_probabilities: Record<string, number> | null;
  ideal_probabilities: Record<string, number>;
  error: string | null;
}

export interface Lesson {
  lesson_id: string;
  title: string;
  description: string;
  content: string;
  difficulty: 'beginner' | 'intermediate';
  learning_objectives: string[];
  related_experiments: string[];
  order: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface HardwareStatus {
  hardware_enabled: boolean;
  daily_limit: number;
  submitted_today: number;
  remaining_today: number;
  active_jobs: number;
  active_limit: number;
  max_shots: number;
}