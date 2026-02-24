"use client";

import { useState } from "react";
import { useRecommendations } from "@/hooks/use-recommendations";
import { DEFAULT_THRESHOLD } from "@/lib/constants";
import { RecommendationCard } from "./recommendation-card";
import { RecommendationDetailDialog } from "./recommendation-detail-dialog";
import { ThresholdSlider } from "@/components/filters/threshold-slider";
import { Skeleton } from "@/components/ui/skeleton";
import type { TenderRecommendation } from "@/types/api";
import { useFeedbackStore } from "@/stores/feedback-store";

export function RecommendationList() {
  const [threshold, setThreshold] = useState(DEFAULT_THRESHOLD);
  const { data, isLoading, isError, error } = useRecommendations(
    undefined,
    threshold
  );

  const [selected, setSelected] = useState<TenderRecommendation | null>(null);
  const feedbacks = useFeedbackStore((s) => s.feedbacks);

  // Client-side re-ranking: boost "relevant", demote "not_relevant"
  const sortedRecommendations = data?.recommendations
    ? [...data.recommendations].sort((a, b) => {
        const fbA = feedbacks[a.tender_url]?.feedback;
        const fbB = feedbacks[b.tender_url]?.feedback;

        const boostA =
          fbA === "relevant" ? 0.1 : fbA === "not_relevant" ? -0.3 : 0;
        const boostB =
          fbB === "relevant" ? 0.1 : fbB === "not_relevant" ? -0.3 : 0;

        return b.score + boostB - (a.score + boostA);
      })
    : [];

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-40 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-600">
          Failed to load recommendations:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold">
            Recommended Tenders
            {data && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({data.total} results)
              </span>
            )}
          </h2>
          {data && (
            <p className="text-sm text-muted-foreground">
              For {data.company}
            </p>
          )}
        </div>
        <ThresholdSlider value={threshold} onChange={setThreshold} />
      </div>

      {sortedRecommendations.length === 0 ? (
        <div className="rounded-lg border bg-muted/50 p-10 text-center">
          <p className="text-muted-foreground">
            No tenders match the current threshold. Try lowering it.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {sortedRecommendations.map((tender) => (
            <RecommendationCard
              key={tender.tender_url}
              tender={tender}
              onClick={() => setSelected(tender)}
            />
          ))}
        </div>
      )}

      <RecommendationDetailDialog
        tender={selected}
        open={!!selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      />
    </div>
  );
}

