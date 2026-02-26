"use client";

import Link from "next/link";
import { useTenderSwipeStore, type SwipedTender } from "@/stores/tender-swipe-store";
import { useTender } from "@/hooks/use-tender";
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
import { TenderChat } from "@/components/tenders/tender-chat";

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

function getFileName(url: string): string {
  const parts = url.split("/");
  const full = decodeURIComponent(parts[parts.length - 1]);
  const withoutTimestamp = full.replace(/^\d{8}T\d+_/, "");
  return withoutTimestamp;
}

function getPlatformName(url: string): string {
  try {
    const hostname = new URL(url).hostname.replace("www.", "");
    return hostname;
  } catch {
    return "źródło";
  }
}

function LikedTenderCard({ item }: { item: SwipedTender }) {
  const { data: details, isLoading } = useTender(item.tender.tender_name);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg leading-snug">
          {item.tender.tender_name}
        </CardTitle>
        {details && (
          <CardDescription className="text-sm">
            {details.organization}
          </CardDescription>
        )}
        {isLoading && (
          <div className="h-4 w-1/3 animate-pulse rounded bg-muted" />
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading && (
          <div className="space-y-2">
            <div className="h-4 w-1/2 animate-pulse rounded bg-muted" />
            <div className="h-4 w-1/3 animate-pulse rounded bg-muted" />
          </div>
        )}

        {details && (
          <div className="space-y-2 text-sm">
            <div className="flex items-start gap-2">
              <span className="shrink-0 text-muted-foreground">Termin składania:</span>
              <span>{details.submission_deadline}</span>
            </div>

            <a
              href={details.tender_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-blue-600 underline underline-offset-2 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Przejdź do [{getPlatformName(details.tender_url)}]
            </a>

            {details.file_urls.length > 0 && (
              <div>
                <span className="text-muted-foreground">
                  Pliki ({details.files_count}):
                </span>
                <ul className="mt-1 space-y-1 pl-4">
                  {details.file_urls.map((url) => (
                    <li key={url}>
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 underline underline-offset-2 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                      >
                        {getFileName(url)}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <hr className="border-border" />
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-muted-foreground">Szczegóły dopasowania:</h4>
          <div className="flex flex-wrap gap-3">
            <MatchBadge level={item.tender.name_match} label="Nazwa" />
            <MatchBadge level={item.tender.industry_match} label="Branża" />
          </div>
        </div>

        <hr className="border-border" />
        <TenderChat tenderName={item.tender.tender_name} />
      </CardContent>
    </Card>
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
            <LikedTenderCard key={item.tender.tender_name} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
