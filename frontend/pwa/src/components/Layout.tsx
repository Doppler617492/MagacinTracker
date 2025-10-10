import { Outlet } from "react-router-dom";

// Layout is now simplified - Header and BottomNav are in individual pages
export const Layout = () => {
  return <Outlet />;
};
