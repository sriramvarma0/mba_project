import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:5000",
});

const AUTH_EXPIRED_EVENT = "mba:auth-expired";

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("mba_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401 || status === 422) {
      localStorage.removeItem("mba_token");
      localStorage.removeItem("mba_user");
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
      }
    }
    return Promise.reject(error);
  }
);

export { AUTH_EXPIRED_EVENT };

export default api;
