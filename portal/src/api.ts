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

const API_BASE = import.meta.env.VITE_API_URL || "";
const REQUEST_TIMEOUT_MS = 25000;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });
    if (res.status === 401) {
      const isLogin = path.includes("/auth/login");
      if (!isLogin) {
        clearToken();
        window.location.reload();
      }
      throw new Error("Invalid credentials");
    }
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

async function upload<T>(path: string, form: FormData): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body: form });
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

export interface CapabilitySnapshot {
  empire: { tier: number; label: string; signals: Record<string, number> };
  effective_rates: { ammo_percent: number; hold_hours: number };
  liquidity: {
    ammo_usd: number;
    float_hold_usd: number;
    total_deployable_usd: number;
  };
  ready_to_order: Array<{ id: number; name: string; category: string; capability: string }>;
  affordable_now: Array<{ id: number; name: string; category: string; reason: string; remaining_usd: number }>;
  next_unlocks: Array<{ id: number; name: string; funded_percent: number; remaining_usd: number }>;
  recommended_actions: string[];
  voice_summary: string;
  how_to_add: { voice: string; api: string; portal: string };
}

export interface Acquisition {
  id: number;
  category: string;
  name: string;
  description: string | null;
  target_cost_cents: number;
  funded_cents: number;
  status: string;
  priority: number;
  empire_tier: number;
  equipment_spec: string | null;
}

export interface AcquisitionCategories {
  categories: Record<string, string>;
}

export interface Lead {
  id: number;
  name: string;
  phone: string;
  email: string | null;
  city: string;
  crisis_type: string;
  status: string;
  created_at: string;
}

export interface SovereignStatus {
  scale: {
    hosts_locked: number;
    slots_remaining: number;
    max_units: number;
    target_cities: number;
    focus_city?: string;
  };
  float_usd: number;
  vault_reserve_usd: number;
}

export interface HealthSnapshot {
  status: string;
  layers: { sara_wired?: boolean; sara_phone?: string; https_base?: string };
  velocity: { launch_mode?: boolean; auto_execute?: boolean };
}

export interface LeadPipeline {
  total: number;
  with_phone: number;
  needs_lookup: number;
  recent: Array<{
    id: number;
    name: string;
    phone: string;
    city: string;
    status: string;
    has_phone: boolean;
  }>;
}

export interface LaunchDeck {
  sara_wired: boolean;
  sara_phone: string;
  leads_in_pipeline: number;
  auto_hunt: boolean;
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
  capability: () => request<CapabilitySnapshot>("/api/treasury/capability"),
  acquisitions: () => request<Acquisition[]>("/api/treasury/acquisitions"),
  acquisitionCategories: () => request<AcquisitionCategories>("/api/treasury/acquisitions/categories"),
  addAcquisition: (body: {
    category: string;
    name: string;
    description?: string;
    target_cost_cents?: number;
    priority?: number;
    empire_tier?: number;
  }) =>
    request<Acquisition>("/api/treasury/acquisitions", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  health: () => request<HealthSnapshot>("/health"),
  leads: () => request<Lead[]>("/api/value-node/leads"),
  addLead: (body: { name: string; phone: string; city: string; email?: string }) =>
    request<Lead>("/api/value-node/leads", { method: "POST", body: JSON.stringify(body) }),
  sovereignStatus: () => request<SovereignStatus>("/api/sovereign-stay/status"),
  presale: (body: {
    host_name: string;
    property_address: string;
    city_grid: string;
    worker_ref: string;
    proof_notes: string;
    dry_run_closer: boolean;
  }) =>
    request<Record<string, unknown>>("/api/sovereign-stay/presale", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  sovereignSimulate: () =>
    request<Record<string, unknown>>("/api/sovereign-stay/simulate", { method: "POST" }),
  readyRoomChat: (message: string) =>
    request<Record<string, unknown>>("/api/ready-room/chat", {
      method: "POST",
      body: JSON.stringify({ message, auto_scan: true }),
    }),
  readyRoomUpload: (file: File, caption: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("caption", caption);
    return upload<Record<string, unknown>>("/api/ready-room/chat/upload", form);
  },
  launchStatus: () => request<LaunchDeck>("/api/launch/status"),
  leadPipeline: () => request<LeadPipeline>("/api/leads/pipeline"),
  huntLeads: (city = "Kansas City", max_leads = 25) =>
    request<Record<string, unknown>>("/api/leads/hunt", {
      method: "POST",
      body: JSON.stringify({ city, max_leads }),
    }),
  killShot: (city = "Kansas City", drill = false) =>
    request<Record<string, unknown>>("/api/launch/kill-shot", {
      method: "POST",
      body: JSON.stringify({ city, hunt_leads: true, max_leads: 25, drill }),
    }),
  ecoStatus: () => request<Record<string, unknown>>("/api/eco-express/status"),
  ecoStrikeList: () =>
    request<Record<string, unknown>>("/api/eco-express/strike-list", { method: "POST" }),
  ecoJobs: () => request<Array<Record<string, unknown>>>("/api/eco-express/jobs"),
  ecoPaymentConfirmed: (jobId: number, payment_proof: string, scheduled_slot = "ASAP") =>
    request<Record<string, unknown>>(`/api/eco-express/jobs/${jobId}/payment-confirmed`, {
      method: "POST",
      body: JSON.stringify({ payment_proof, scheduled_slot, dry_run: false }),
    }),
};
