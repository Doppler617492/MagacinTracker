import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useQueryClient } from '@tanstack/react-query';

const socketEndpoint = import.meta.env.VITE_SOCKET_URL ?? window.location.origin;

export const useWebSocket = (queryKeys: string[]) => {
  const queryClient = useQueryClient();
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    socketRef.current = io(socketEndpoint, { path: "/ws" });
    
    socketRef.current.on("connect", () => {
      console.info("Admin WebSocket connected", socketRef.current?.id);
    });

    // Listen for TV delta events (real-time updates)
    socketRef.current.on("tv_delta", (data) => {
      console.info("Admin WebSocket received tv_delta", data);
      
      // Invalidate relevant queries to trigger refetch
      queryKeys.forEach(queryKey => {
        // Invalidate all queries with this prefix
        // This will match ["trebovanja"], ["trebovanje"], ["trebovanje", <id>], etc.
        queryClient.invalidateQueries({ 
          predicate: (query) => {
            const key = query.queryKey[0];
            return key === queryKey || (typeof key === 'string' && key.startsWith(queryKey));
          }
        });
      });
    });

    socketRef.current.on("disconnect", () => {
      console.info("Admin WebSocket disconnected");
    });

    // Cleanup on unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [queryClient, queryKeys]);

  return socketRef.current;
};
