"use client";

import Link from "next/link";
import { useTenderSwipeStore } from "@/stores/tender-swipe-store";
import type { MatchLevel } from "@/types/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const matchLabels: Record<MatchLevel, string> = {
  PERFECT_MATCH: "Idealne",
  PARTIAL_MATCH: "Czesciowe",
  DONT_KNOW: "Niepewne",
  NO_MATCH: "Brak",
};

const matchColors: Record<MatchLevel, string> = {
  PERFECT_MATCH:
    "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  PARTIAL_MATCH:
    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  DONT_KNOW:
    "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
  NO_MATCH:
    "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

function MatchBadge({ level, label }: { level: MatchLevel; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">{label}:</span>
      <span
        className={cn(
          "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
          matchColors[level]
        )}
      >
        {matchLabels[level]}
      </span>
    </div>
  );
}

export default function LikedTendersPage() {
  const { getLiked } = useTenderSwipeStore();
  const liked = getLiked().sort((a, b) => b.timestamp - a.timestamp);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Polubione przetargi</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {liked.length}{" "}
            {liked.length === 1
              ? "przetarg"
              : liked.length < 5
                ? "przetargi"
                : "przetargów"}
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/tenders">Wróć do przeglądania</Link>
        </Button>
      </div>

      {liked.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Brak polubionych przetargów</CardTitle>
            <CardDescription>
              Przejrzyj rekomendacje i polub przetargi, które Cię interesują.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/tenders">Przeglądaj przetargi</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {liked.map((item) => (
            <Card key={item.tender.tender_name}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base leading-snug">
                  {item.tender.tender_name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-3">
                    <MatchBadge
                      level={item.tender.name_match}
                      label="Nazwa"
                    />
                    <MatchBadge
                      level={item.tender.industry_match}
                      label="Branża"
                    />
                  </div>
                  {item.tender.name_reason && (
                    <p className="text-xs text-muted-foreground">
                      {item.tender.name_reason}
                    </p>
                  )}
                  {item.tender.industry_reason && (
                    <p className="text-xs text-muted-foreground">
                      {item.tender.industry_reason}
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
