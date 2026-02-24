"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScoreBadge } from "./score-badge";
import { FeedbackButtons } from "./feedback-buttons";
import type { TenderRecommendation } from "@/types/api";

interface RecommendationDetailDialogProps {
  tender: TenderRecommendation | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RecommendationDetailDialog({
  tender,
  open,
  onOpenChange,
}: RecommendationDetailDialogProps) {
  if (!tender) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="leading-tight">{tender.name}</DialogTitle>
          <DialogDescription>
            {tender.organization} • {tender.industry}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <ScoreBadge score={tender.score} />
            <FeedbackButtons tenderUrl={tender.tender_url} />
          </div>

          <div>
            <h4 className="mb-1 text-sm font-medium">Why this is relevant</h4>
            <p className="text-sm text-muted-foreground">{tender.reasoning}</p>
          </div>

          <a
            href={tender.tender_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-primary underline-offset-4 hover:underline"
          >
            Open tender page →
          </a>
        </div>
      </DialogContent>
    </Dialog>
  );
}

