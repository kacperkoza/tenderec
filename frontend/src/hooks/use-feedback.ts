"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getFeedbacks, createFeedback } from "@/lib/api-client";
import type { CreateFeedbackRequest } from "@/types/api";

export function useFeedbacks(company: string) {
  return useQuery({
    queryKey: ["feedbacks", company],
    queryFn: () => getFeedbacks(company),
    enabled: !!company,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useCreateFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      company,
      data,
    }: {
      company: string;
      data: CreateFeedbackRequest;
    }) => createFeedback(company, data),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["feedbacks", variables.company],
      });
    },
  });
}
