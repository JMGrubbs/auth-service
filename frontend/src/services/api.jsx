import axios from "axios";

const AUTH_URL = import.meta.env.VITE_AUTH_SERVICE_BACKEND_URL;
export const SESSION_EXPIRED_EVENT = "watchtower:session-expired";

export const api = axios.create({
  baseURL: AUTH_URL,
  withCredentials: true,
});

export const notifySessionExpired = () => {
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
};
