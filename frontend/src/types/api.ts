export const EXPERIMENT_IDS = [
  'superposition', 'bell_entanglement', 'interference', 'phase_kickback',
  'ghz_entanglement', 'deutsch_jozsa', 'grover_search', 'qft_phase',
  'quantum_teleportation', 'bit_flip_correction',
] as const;
export type ExperimentId = typeof EXPERIMENT_IDS[number];
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';

export interface ExperimentGate {
  name: string;
  qubits: number[];
  explanation: string;
  classical_bits?: number[];
  angle?: number;
  label?: string;
}

export interface Experiment {
  experiment_id: ExperimentId;
  title: string;
  description: string;
  qubits: number;
  classical_bits: number;
  difficulty: Difficulty;
  lesson_id: string;
  gates: ExperimentGate[];
  qiskit_code: string;
  interpretation: string;
  next_experiment?: ExperimentId | null;
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
  amplitudes?: { outcome: string; real: number; imag: number; probability: number; phase_degrees: number }[];
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

export interface PracticeQuestion {
  question_id: string;
  kind: 'multiple_choice' | 'short_answer';
  prompt: string;
  options: { option_id: string; text: string }[];
}

export type PracticeFeedback = {
  question_id: string;
  kind: 'multiple_choice';
  correct: boolean;
  correct_option_id: string;
  explanation: string;
} | {
  question_id: string;
  kind: 'short_answer';
  sample_answer: string;
  key_points: string[];
};

export interface Lesson {
  lesson_id: string;
  title: string;
  description: string;
  content: string;
  difficulty: Difficulty;
  learning_objectives: string[];
  related_experiments: string[];
  order: number;
  prerequisites?: string[];
  references?: { title: string; url: string }[];
  practice_questions?: PracticeQuestion[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  source?: 'llm' | 'fallback';
  notice?: string | null;
}

export interface AssistantResponse {
  reply: string;
  source: 'llm' | 'fallback';
  notice?: string | null;
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
export interface PublicConfig {
  hardware_enabled: boolean;
  max_simulator_shots: number;
  max_hardware_shots: number;
  default_shots: number;
}
