import { createContext, useContext, useEffect, useState } from "react";
import { api, auth } from "./api";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(auth.user());

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener("auth-expired", onExpired);
    return () => window.removeEventListener("auth-expired", onExpired);
  }, []);

  const login = async (email, password) => {
    const data = await api.login({ email, password });
    auth.save(data.access_token, data.user);
    setUser(data.user);
    return data.user;
  };
  const logout = async () => {
    try { await api.logout(); } catch { /* token may already be invalid */ }
    auth.clear();
    setUser(null);
  };
  return <Ctx.Provider value={{ user, login, logout }}>{children}</Ctx.Provider>;
}
