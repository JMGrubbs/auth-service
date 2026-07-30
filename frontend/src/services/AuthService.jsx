import { api } from "./api";

export const loginUser = async (email, password) => {
  try {
    const response = await api.post("/api/v1/auth/login", { email, password });
    return response.data;
  } catch (error) {
    console.error("Error logging in user:", error);
    throw error;
  }
};

export const registerUser = async (email, password) => {
  try {
    const response = await api.post("/api/v1/users/create", { email, password });
    return response.data;
  } catch (error) {
    console.error("Error registering user:", error);
    throw error;
  }
};

export const logoutUser = async () => {
  try {
    const response = await api.post("/api/v1/auth/logout");
    return response.data;
  } catch (error) {
    console.error("Error logging out user:", error);
    throw error;
  }
};
