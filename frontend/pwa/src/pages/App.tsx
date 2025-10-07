import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import TaskDetailPage from "./TaskDetailPage";
import TasksPage from "./TasksPage";
import OfflineQueueComponent from "../components/OfflineQueue";
import { Route, Routes } from "react-router-dom";
import { ensureAuth } from "../api";

const App = () => {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    ensureAuth()
      .then(() => setReady(true))
      .catch((error) => console.error("Auth bootstrap failed", error));
  }, []);

  if (!ready) {
    return <div className="card">Priprema aplikacije...</div>;
  }

  return (
    <>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<TasksPage />} />
          <Route path="tasks/:id" element={<TaskDetailPage />} />
        </Route>
      </Routes>
      <OfflineQueueComponent />
    </>
  );
};

export default App;
