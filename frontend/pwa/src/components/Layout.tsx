import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";

export const Layout = () => {
  const [online, setOnline] = useState<boolean>(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/">Magacin Worker</Link>
        <span className={`status-dot ${online ? "online" : "offline"}`}>{online ? "Online" : "Offline"}</span>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
};
