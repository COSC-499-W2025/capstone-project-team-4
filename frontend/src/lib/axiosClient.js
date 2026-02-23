import axios from "axios";

// This is for communicating with the backend.
// Instead of having to input the url (as it can change depending on the environment), just use an environment variable
const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  //   For auth stuff in the future. This enables auth so that we don't have to worry about that later
  withCredentials: true,
});

export default axiosClient;
