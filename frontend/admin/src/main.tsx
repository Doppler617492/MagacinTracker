import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./pages/App";
import ErrorBoundary from "./components/ErrorBoundary";
import "antd/dist/reset.css";
import "./styles.css";

console.log("🚀 Starting Magacin Admin...");

const queryClient = new QueryClient();

console.log("🔧 About to render React app...");

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element not found");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
);

console.log("✅ React App rendered successfully!");
