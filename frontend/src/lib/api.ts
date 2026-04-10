import axios, { AxiosInstance } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
});

// Auth interceptor
api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Refresh token on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${API_BASE}/api/v1/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem("access_token", res.data.access_token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api.request(error.config);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/auth/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// API helpers
export const authApi = {
  login:    (email: string, password: string) => api.post("/auth/login", { email, password }),
  register: (data: any) => api.post("/auth/register", data),
  me:       () => api.get("/auth/me"),
};

export const matchesApi = {
  list:        (params?: any) => api.get("/matches", { params }),
  get:         (id: string)   => api.get(`/matches/${id}`),
  create:      (data: any)    => api.post("/matches", data),
  updateStatus:(id: string, status: string) => api.put(`/matches/${id}/status?new_status=${status}`),
  listEvents:  (id: string)   => api.get(`/matches/${id}/events`),
  createEvent: (id: string, data: any) => api.post(`/matches/${id}/events`, data),
};

export const videosApi = {
  list:          (params?: any) => api.get("/videos", { params }),
  get:           (id: string)   => api.get(`/videos/${id}`),
  upload:        (form: FormData, onProgress?: (pct: number) => void) =>
    api.post("/videos/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / (e.total || 1))),
    }),
  ingestUrl:     (data: any) => api.post("/videos/ingest-url", data),
  getStatus:     (id: string) => api.get(`/videos/${id}/status`),
  getStreamUrl:  (id: string) => api.get(`/videos/${id}/stream-url`),
};

export const clipsApi = {
  list:          (params?: any) => api.get("/clips", { params }),
  get:           (id: string)   => api.get(`/clips/${id}`),
  create:        (data: any)    => api.post("/clips", data),
  publish:       (id: string, isPublic: boolean) => api.put(`/clips/${id}/publish?is_public=${isPublic}`),
  getShared:     (token: string) => api.get(`/clips/shared/${token}`),
  listAnnotations: (id: string) => api.get(`/clips/${id}/annotations`),
  createAnnotation:(id: string, data: any) => api.post(`/clips/${id}/annotations`, data),
};

export const analyticsApi = {
  getMatchAnalytics:   (matchId: string) => api.get(`/analytics/matches/${matchId}`),
  getPlayerStats:      (matchId: string) => api.get(`/analytics/matches/${matchId}/players`),
  getShotMap:          (matchId: string, params?: any) => api.get(`/analytics/matches/${matchId}/shots`, { params }),
  coachAssist:         (matchId: string, question: string) => api.post("/analytics/coach-assist", { match_id: matchId, question }),
};

export const teamsApi = {
  list:       () => api.get("/teams"),
  get:        (id: string) => api.get(`/teams/${id}`),
  create:     (data: any) => api.post("/teams", data),
  listPlayers:(teamId: string) => api.get(`/teams/${teamId}/players`),
  addPlayer:  (teamId: string, data: any) => api.post(`/teams/${teamId}/players`, data),
};

export const livestreamApi = {
  start:    (data: any) => api.post("/livestream/start", data),
  stop:     (matchId: string) => api.post(`/livestream/stop/${matchId}`),
  status:   (matchId: string) => api.get(`/livestream/status/${matchId}`),
  bookmark: (matchId: string, label: string) => api.post(`/livestream/bookmark/${matchId}?label=${label}`),
};
