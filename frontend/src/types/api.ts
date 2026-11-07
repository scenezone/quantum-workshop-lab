import {
  CUSTOM_GATES,
  EXPERIMENT_IDS,
  MEASUREMENT_BASES,
  NOISE_PROFILES,
} from './catalog.generated';

export { EXPERIMENT_IDS };
export type ExperimentId = typeof EXPERIMENT_IDS[number];
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';
export type CircuitGateName = keyof typeof CUSTOM_GATES;
export type NoiseProfile = typeof NOISE_PROFILES[number]['id'];
export type MeasurementBasis = typeof MEASUREMENT_BASES[number];

export interface CustomCircuitGate {
  name: CircuitGateName;
  qubits: number[];
  /** Rotation angle, or θ for U. */
  angle?: number;
  phi?: number;
  lam?: number;
}

export interface CustomCircuitDefinition {
  qubits: number;
  gates: CustomCircuitGate[];
}

export interface CustomCircuitInput extends CustomCircuitDefinition {
  shots: number;
  noise_profile: NoiseProfile;
  measurement_bases?: MeasurementBasis[];
}

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

export interface Amplitude {
  outcome: string;
  real: number;
  imag: number;
  probability: number;
  phase_degrees: number;
}

export interface ExperimentResult {
  experiment_id: string;
  backend: 'aer_simulator' | 'ibm_quantum' | 'ibm_quantum_recorded';
  backend_name: string | null;
  shots: number;
  noise_profile?: NoiseProfile | null;
  measurement_bases?: MeasurementBasis[] | null;
  counts: Record<string, number>;
  observed_probabilities: Record<string, number>;
  ideal_probabilities: Record<string, number>;
  provider_job_id: string | null;
  tracking_id: string | null;
  recorded_at?: string | null;
  amplitudes?: Amplitude[] | null;
}

export interface BlochVector {
  qubit: number;
  x: number;
  y: number;
  z: number;
  /** Below 1 when the qubit is entangled with others. */
  length?: number;
}

export interface StateEvolutionStep {
  step: number;
  gate: string;
  explanation: string;
  qubits: BlochVector[];
}

export interface ExperimentEvolution {
  experiment_id: string;
  qubits: number;
  steps: StateEvolutionStep[];
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
  transpiled_depth?: number | null;
  two_qubit_gate_count?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PracticeQuestion {
  question_id: string;
  kind: 'multiple_choice' | 'short_answer';
  prompt: string;
  options: { option_id: string; text: string }[];
}

export interface AIWrittenFeedback {
  covered_points: string[];
  missing_points: string[];
  feedback: string;
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
  ai_feedback?: AIWrittenFeedback | null;
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
  streaming?: boolean;
}

export type AssistantMode = 'explain' | 'hint' | 'quiz';

export interface AssistantResponse {
  reply: string;
  source: 'llm' | 'fallback';
  notice?: string | null;
}

export interface HardwareStatus {
  hardware_enabled: boolean;
  configured_accounts?: number;
  daily_limit: number;
  submitted_today: number;
  remaining_today: number;
  active_jobs: number;
  active_limit: number;
  max_shots: number;
}

export interface NoiseProfileInfo {
  id: NoiseProfile;
  label: string;
  kind: 'preset' | 'device';
}

export interface PublicConfig {
  hardware_enabled: boolean;
  max_simulator_shots: number;
  max_hardware_shots: number;
  default_shots: number;
  database_enabled?: boolean;
  feedback_enabled?: boolean;
  sessions_enabled?: boolean;
  live_ai_enabled?: boolean;
  noise_profiles?: NoiseProfileInfo[];
}

export interface BuildChallenge {
  challenge_id: string;
  title: string;
  objective: string;
  difficulty: Difficulty;
  qubits: number;
  allowed_gates: CircuitGateName[];
  max_gates: number;
  hint: string;
  kind: 'state' | 'distribution';
}

export interface ChallengeCheckResult {
  challenge_id: string;
  passed: boolean;
  score: number;
  metric: 'fidelity' | 'distribution_match';
  message: string;
}

export interface ChshSetting {
  alice_angle: number;
  bob_angle: number;
  counts: Record<string, number>;
  correlation: number;
  ideal_correlation: number;
}

export interface ChshResult {
  shots: number;
  noise_profile: NoiseProfile;
  backend_name: string;
  settings: ChshSetting[];
  s_value: number;
  s_standard_error: number;
  ideal_s_value: number;
  classical_bound: number;
  quantum_bound: number;
}

export type VqeHamiltonian = 'zx' | 'h2';

export interface VqeResult {
  hamiltonian: VqeHamiltonian;
  description: string;
  terms: [string, number][];
  parameter_count: number;
  ground_energy: number;
  final_parameters: number[];
  final_energy: number;
  trace: { iteration: number; parameters: number[]; energy: number; exact_energy: number }[];
  landscape: { theta: number; energy: number }[];
  backend_name: string;
}

export interface WorkshopSession {
  code: string;
  name: string;
  created_at: string;
  expires_at: string;
}

export interface SessionMembership {
  session: WorkshopSession;
  participant_id: string;
  participant_token: string;
}

export interface FeedbackSummary {
  count: number;
  average_rating: number | null;
  average_clarity: number | null;
  completion_rate: number | null;
  rating_distribution: Record<string, number>;
  recent_comments: { comments: string; rating: number; created_at: string }[];
}

export interface SessionDashboard {
  session: WorkshopSession;
  participant_count: number;
  participants: {
    participant_id: string;
    nickname: string;
    completed_lessons: number;
    completed_challenges: number;
    practice_correct: number;
    practice_attempted: number;
    last_seen: string;
  }[];
  lesson_completion: { lesson_id: string; title: string; completed: number }[];
  challenge_completion: Record<string, number>;
  feedback: FeedbackSummary;
}
