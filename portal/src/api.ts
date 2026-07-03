const API_BASE = import.meta.env.VITE_API_URL || "";

export function getToken(): string | null {
  return localStorage.getItem("cc_token");
}

export function setToken(token: string) {
  localStorage.setItem("cc_token", token);
}

export function clearToken() {
  localStorage.removeItem("cc_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    window.location.reload();
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export interface DashboardStats {
  tasks_pending: number;
  tasks_in_progress: number;
  tasks_completed: number;
  decisions_pending: number;
  voice_sessions_today: number;
  recent_activity_count: number;
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: number;
  event_type: string;
  message: string;
  metadata_json: string | null;
  created_at: string;
}

export interface Decision {
  id: number;
  title: string;
  context: string;
  recommendation: string | null;
  status: string;
  created_at: string;
  resolved_at: string | null;
}

export interface VoiceSession {
  id: number;
  vapi_call_id: string | null;
  summary: string | null;
  transcript: string | null;
  duration_seconds: number | null;
  started_at: string;
  ended_at: string | null;
}

export interface Briefing {
  greeting: string;
  stats: DashboardStats;
  pending_tasks: Task[];
  pending_decisions: Decision[];
  recent_activity: Activity[];
}

export async function login(username: string, password: string) {
  const data = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(data.access_token);
}

export const api = {
  briefing: () => request<Briefing>("/api/briefing"),
  tasks: () => request<Task[]>("/api/tasks"),
  activity: () => request<Activity[]>("/api/activity"),
  decisions: () => request<Decision[]>("/api/decisions"),
  voiceSessions: () => request<VoiceSession[]>("/api/voice-sessions"),
};
