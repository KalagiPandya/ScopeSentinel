import { createContext, useContext, useState, useEffect } from "react";
import { auth } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("scopesentinel_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("scopesentinel_token");
    if (!token) {
      setLoading(false);
      return;
    }
    auth
      .me()
      .then((res) => {
        setUser(res.data);
        localStorage.setItem("scopesentinel_user", JSON.stringify(res.data));
      })
      .catch(() => {
        localStorage.removeItem("scopesentinel_token");
        localStorage.removeItem("scopesentinel_user");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const res = await auth.login(email, password);
    const { access_token, user_id, name, role } = res.data;
    localStorage.setItem("scopesentinel_token", access_token);
    const userObj = { id: user_id, name, role, email };
    localStorage.setItem("scopesentinel_user", JSON.stringify(userObj));
    setUser(userObj);
    return userObj;
  };

  const logout = () => {
    localStorage.removeItem("scopesentinel_token");
    localStorage.removeItem("scopesentinel_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
