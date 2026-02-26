"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCompany, createCompany, NotFoundError } from "@/lib/api-client";
import type { CreateCompanyRequest } from "@/types/api";

export function useCompany(name: string) {
  return useQuery({
    queryKey: ["company", name],
    queryFn: () => getCompany(name),
    enabled: !!name,
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error) => {
      if (error instanceof NotFoundError) return false;
      return failureCount < 2;
    },
  });
}

export function useCreateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      name,
      data,
    }: {
      name: string;
      data: CreateCompanyRequest;
    }) => createCompany(name, data),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["company", variables.name],
      });
    },
  });
}
