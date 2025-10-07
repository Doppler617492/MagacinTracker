import { useQuery } from "@tanstack/react-query";
import { Progress } from "antd";
import { Link } from "react-router-dom";
import client from "../api";

interface TaskCard {
  id: string;
  dokument: string;
  lokacija: string;
  progress: number;
  stavke_total: number;
  status: string;
  due_at?: string;
}

const fetchTasks = async (): Promise<TaskCard[]> => {
  const { data } = await client.get("/worker/tasks");
  return data;
};

const statusLabel: Record<string, string> = {
  assigned: "Dodijeljen",
  in_progress: "U toku",
  done: "Završen",
  blocked: "Blokiran"
};

const TasksPage = () => {
  const { data, isLoading } = useQuery({ queryKey: ["worker", "tasks"], queryFn: fetchTasks });

  if (isLoading) {
    return <p>Učitavanje zadataka...</p>;
  }

  if (!data || data.length === 0) {
    return <p>Trenutno nema aktivnih zadataka.</p>;
  }

  return (
    <div>
      <h1>Moji zadaci</h1>
      {(data ?? []).map((task) => (
        <Link to={`/tasks/${task.id}`} key={task.id} className="card">
          <div className="card-header">
            <div>
              <strong>Dokument:</strong> {task.dokument}
            </div>
            <span className={`status ${task.status}`}>{statusLabel[task.status] ?? task.status}</span>
          </div>
          <div>
            <strong>Lokacija:</strong> {task.lokacija}
          </div>
          {task.due_at ? (
            <div>
              <strong>Rok:</strong> {new Date(task.due_at).toLocaleString()}
            </div>
          ) : null}
          <div style={{ marginTop: 12 }}>
            <Progress percent={Math.round(task.progress)} showInfo={false} strokeColor="#4ade80" />
            <small>
              Napredak: {Math.round(task.progress)}% • Stavke: {task.stavke_total}
            </small>
          </div>
        </Link>
      ))}
    </div>
  );
};

export default TasksPage;
