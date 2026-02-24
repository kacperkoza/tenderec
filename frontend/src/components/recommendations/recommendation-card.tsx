"use client";

import { ExternalLink } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScoreBadge } from "./score-badge";
import { FeedbackButtons } from "./feedback-buttons";
import type { TenderRecommendation } from "@/types/api";

interface RecommendationCardProps {
  tender: TenderRecommendation;
  onClick?: () => void;
}

export function RecommendationCard({
  tender,
  onClick,
}: RecommendationCardProps) {
  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base leading-tight">
            {tender.name}
          </CardTitle>
          <ScoreBadge score={tender.score} />
        </div>
        <CardDescription className="flex items-center gap-2">
          <span>{tender.organization}</span>
          <span className="text-xs">•</span>
          <span className="text-xs capitalize">{tender.industry}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="line-clamp-2 text-sm text-muted-foreground">
          {tender.reasoning}
        </p>
        <div className="mt-3 flex items-center justify-between">
          <FeedbackButtons tenderUrl={tender.tender_url} />
          <a
            href={tender.tender_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <ExternalLink className="h-3 w-3" />
            View tender
          </a>
        </div>
      </CardContent>
    </Card>
  );
}

