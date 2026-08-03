import { api } from "./api";

export const getCurrentUser = async () => {
  try {
    const response = await api.get("/api/v1/auth/me");
    return response.data;
  } catch (error) {
    console.error("Error fetching current user:", error);
    throw error;
  }
};