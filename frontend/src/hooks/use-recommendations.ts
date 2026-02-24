import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { DEFAULT_COMPANY_ID } from "@/lib/constants";

export function useRecommendations(
  companyId: string = DEFAULT_COMPANY_ID,
  threshold?: number
) {
  return useQuery({
    queryKey: ["recommendations", companyId, threshold],
    queryFn: () => apiClient.getRecommendations(companyId, threshold),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

