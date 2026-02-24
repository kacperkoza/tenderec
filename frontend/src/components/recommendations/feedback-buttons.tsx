"use client";

import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFeedbackStore } from "@/stores/feedback-store";
import { cn } from "@/lib/utils";

interface FeedbackButtonsProps {
  tenderUrl: string;
}

export function FeedbackButtons({ tenderUrl }: FeedbackButtonsProps) {
  const { getFeedback, setFeedback } = useFeedbackStore();
  const current = getFeedback(tenderUrl);

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={(e) => {
          e.stopPropagation();
          setFeedback(tenderUrl, current === "relevant" ? null : "relevant");
        }}
        className={cn(
          "h-8 w-8 p-0",
          current === "relevant" && "bg-green-100 text-green-700"
        )}
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={(e) => {
          e.stopPropagation();
          setFeedback(
            tenderUrl,
            current === "not_relevant" ? null : "not_relevant"
          );
        }}
        className={cn(
          "h-8 w-8 p-0",
          current === "not_relevant" && "bg-red-100 text-red-700"
        )}
      >
        <ThumbsDown className="h-4 w-4" />
      </Button>
    </div>
  );
}

