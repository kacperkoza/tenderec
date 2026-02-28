"use client";

import { useMutation } from "@tanstack/react-query";
import { askTenderQuestion } from "@/lib/api-client";

const COMPANY_NAME = "greenworks";

export function useTenderChat(tenderName: string) {
  return useMutation({
    mutationFn: (question: string) =>
      askTenderQuestion({
        tender_name: tenderName,
        question,
        company_name: COMPANY_NAME,
      }),
  });
}
