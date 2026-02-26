"use client";

import { useQuery } from "@tanstack/react-query";
import { getRecommendations } from "@/lib/api-client";
import type { RecommendationsParams } from "@/types/api";

export function useRecommendations(params: RecommendationsParams) {
  return useQuery({
    queryKey: ["recommendations", params],
    queryFn: () => getRecommendations(params),
    enabled: !!params.company,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}
