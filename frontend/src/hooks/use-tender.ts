"use client";

import { useQuery } from "@tanstack/react-query";
import { getTender, NotFoundError } from "@/lib/api-client";

export function useTender(name: string, enabled = true) {
  return useQuery({
    queryKey: ["tender", name],
    queryFn: () => getTender(name),
    enabled: !!name && enabled,
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error) => {
      if (error instanceof NotFoundError) return false;
      return failureCount < 2;
    },
  });
}
