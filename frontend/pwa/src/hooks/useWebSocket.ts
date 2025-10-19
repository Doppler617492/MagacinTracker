import { useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";
import { useQueryClient } from "@tanstack/react-query";

const socketEndpoint = import.meta.env.VITE_API_URL ?? window.location.origin;

export const useWebSocket = (queryKeys: string[]) => {
  const queryClient = useQueryClient();
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Get token from localStorage (PWA uses localStorage for auth)
    const token = localStorage.getItem("auth_token");
    if (!token) return;

    socketRef.current = io(socketEndpoint, {
      path: "/ws",
      auth: {
        token: token,
      },
      transports: ["websocket"],
    });

    socketRef.current.on("connect", () => {
      console.info("PWA WebSocket connected", socketRef.current?.id);
    });

    socketRef.current.on("tv_delta", (data) => {
      console.info("PWA WebSocket received tv_delta", data);
      
      // Invalidate relevant queries to trigger refetch
      queryKeys.forEach(queryKey => {
        // Invalidate all queries with this prefix
        queryClient.invalidateQueries({ 
          predicate: (query) => {
            const key = query.queryKey[0];
            return key === queryKey || (typeof key === 'string' && key.startsWith(queryKey));
          }
        });
      });
    });

    socketRef.current.on("disconnect", () => {
      console.info("PWA WebSocket disconnected");
    });

    socketRef.current.on("connect_error", (err) => {
      console.error("PWA WebSocket connection error:", err.message);
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, [queryClient, queryKeys]);

  return socketRef.current;
};
