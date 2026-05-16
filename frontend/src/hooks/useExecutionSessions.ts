import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchExecutionSessions, startExecutionSession, stopExecutionSession } from "@/lib/api";

function snakeToCamelObj(obj: any): any {
  if (Array.isArray(obj)) return obj.map(snakeToCamelObj);
  if (obj === null || typeof obj !== "object") return obj;
  const result: any = {};
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
    result[camelKey] = snakeToCamelObj(value);
  }
  return result;
}

export function useExecutionSessions(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["execution-sessions"],
    queryFn: async () => {
      const res = await fetchExecutionSessions();
      return snakeToCamelObj(res.data);
    },
    enabled: options?.enabled !== false,
  });
}

export function useStartExecutionSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: startExecutionSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["execution-sessions"] });
    },
  });
}

export function useStopExecutionSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: stopExecutionSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["execution-sessions"] });
    },
  });
}
