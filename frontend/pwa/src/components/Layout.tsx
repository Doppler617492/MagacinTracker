import { Outlet } from "react-router-dom";
import Header from "./Header";

// Layout includes sticky header and page content
export const Layout = () => {
  return (
    <>
      <Header />
      <div style={{ paddingTop: '56px' }}> {/* Offset for sticky header */}
        <Outlet />
      </div>
    </>
  );
};
