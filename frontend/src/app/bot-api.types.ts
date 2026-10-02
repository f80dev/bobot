export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  history?: ChatMessage[] | null;
}

export interface SourceHit {
  title: string;
  source: string;
  score: number;
}

export interface TrajectoryStep {
  action: string;
  args?: Record<string, unknown>;
  result?: unknown;
}

export interface ChatResponse {
  answer: string;
  sources: SourceHit[];
  emergency: boolean;
  trajectory: TrajectoryStep[];
}

export interface HealthResponse {
  status: string;
  llm_mock: boolean;
  max_iters: number;
  knowledge_dir: string;
}