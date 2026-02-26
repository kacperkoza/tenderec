"use client";

import { useMemo, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { useRecommendations } from "@/hooks/use-recommendations";
import { useCreateFeedback } from "@/hooks/use-feedback";
import {
  useTenderSwipeStore,
  type SwipeDirection,
} from "@/stores/tender-swipe-store";
import { TinderCard, SwipeButtons } from "@/components/tenders/tinder-card";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { MatchLevel, TenderRecommendation } from "@/types/api";

const NAME_MATCH_LEVELS: MatchLevel[] = [
  "PERFECT_MATCH",
  "PARTIAL_MATCH",
  "DONT_KNOW",
];

const MATCH_LEVEL_LABELS: Record<MatchLevel, string> = {
  PERFECT_MATCH: "Idealne dopasowanie",
  PARTIAL_MATCH: "Częściowe dopasowanie",
  DONT_KNOW: "Trudno ocenić",
  NO_MATCH: "Brak dopasowania",
};

export default function TendersPage() {
  const router = useRouter();
  const [nameMatchIndex, setNameMatchIndex] = useState(0);
  const currentNameMatch = NAME_MATCH_LEVELS[nameMatchIndex];

  const { data, isLoading, error, refetch } = useRecommendations({
    company: "greenworks",
    name_match: currentNameMatch,
  });

  const { swiped, swipe, getLiked, clearAll } = useTenderSwipeStore();
  const { mutate: sendFeedback, isPending: isSendingFeedback } =
    useCreateFeedback();

  const [rejectedTender, setRejectedTender] =
    useState<TenderRecommendation | null>(null);
  const [feedbackText, setFeedbackText] = useState("");

  const unswiped = useMemo(() => {
    if (!data?.recommendations) return [];
    return data.recommendations.filter((r) => !swiped[r.tender_name]);
  }, [data, swiped]);

  const visibleCards = unswiped.slice(0, 2);

  const handleSwipe = useCallback(
    (direction: SwipeDirection) => {
      const current = visibleCards[0];
      if (!current) return;

      if (direction === "left") {
        setRejectedTender(current);
        setFeedbackText("");
      } else {
        swipe(current, direction);
      }
    },
    [visibleCards, swipe]
  );

  function dismissRejectDialog() {
    if (!rejectedTender) return;
    swipe(rejectedTender, "left");
    setRejectedTender(null);
    setFeedbackText("");
  }

  function handleSendFeedback() {
    if (!rejectedTender || !feedbackText.trim()) return;

    const comment = `[Odrzucony przetarg: ${rejectedTender.tender_name}] ${feedbackText.trim()}`;
    sendFeedback(
      { company: "greenworks", data: { feedback_comment: comment } },
      {
        onSettled: () => {
          dismissRejectDialog();
        },
      }
    );
  }

  const liked = getLiked();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-md">
        <Card>
          <CardContent className="py-12">
            <div className="space-y-4">
              <div className="h-6 w-2/3 animate-pulse rounded bg-muted" />
              <div className="h-4 w-full animate-pulse rounded bg-muted" />
              <div className="h-4 w-3/4 animate-pulse rounded bg-muted" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-md">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Błąd</CardTitle>
            <CardDescription>{error.message}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => refetch()}>
              Spróbuj ponownie
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const allDone = visibleCards.length === 0;
  const hasNextLevel = nameMatchIndex < NAME_MATCH_LEVELS.length - 1;
  const isLastLevel = !hasNextLevel;

  function loadNextLevel() {
    if (hasNextLevel) {
      setNameMatchIndex((prev) => prev + 1);
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Rekomendowane przetargi</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Przesuń w prawo aby polubić, w lewo aby odrzucić
        </p>
        <p className="mt-1 text-xs font-medium text-primary">
          {MATCH_LEVEL_LABELS[currentNameMatch]}
        </p>
      </div>

      {allDone ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {isLastLevel
                ? "Przejrzano wszystko!"
                : `Koniec z: ${MATCH_LEVEL_LABELS[currentNameMatch]}`}
            </CardTitle>
            <CardDescription>
              {liked.length > 0 && (
                <span>
                  Polubiono {liked.length}{" "}
                  {liked.length === 1
                    ? "przetarg"
                    : liked.length < 5
                      ? "przetargi"
                      : "przetargów"}
                  .{" "}
                </span>
              )}
              {hasNextLevel ? (
                <span>
                  Załadować przetargi z kategorii:{" "}
                  <strong>
                    {MATCH_LEVEL_LABELS[NAME_MATCH_LEVELS[nameMatchIndex + 1]]}
                  </strong>
                  ?
                </span>
              ) : (
                <span>
                  {liked.length > 0
                    ? "Czy chcesz przejść do listy polubionych przetargów?"
                    : "Nie polubiono żadnych przetargów."}
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {hasNextLevel && (
              <Button onClick={loadNextLevel}>
                Załaduj: {MATCH_LEVEL_LABELS[NAME_MATCH_LEVELS[nameMatchIndex + 1]]}
              </Button>
            )}
            {liked.length > 0 && (
              <Button
                variant={hasNextLevel ? "outline" : "default"}
                onClick={() => router.push("/tenders/liked")}
              >
                Przejdź do polubionych
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => {
                clearAll();
                setNameMatchIndex(0);
              }}
            >
              Zacznij od nowa
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="relative mx-auto h-[380px] w-full">
            {visibleCards.map((tender, i) => (
              <TinderCard
                key={tender.tender_name}
                tender={tender}
                onSwipe={handleSwipe}
                isTop={i === 0}
              />
            ))}
          </div>

          <SwipeButtons onSwipe={handleSwipe} disabled={allDone} />

          <p className="text-center text-xs text-muted-foreground">
            {unswiped.length} z {data?.recommendations.length ?? 0} pozostało
          </p>
        </>
      )}

      <Dialog
        open={rejectedTender !== null}
        onOpenChange={(open) => {
          if (!open) dismissRejectDialog();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Dlaczego odrzucasz ten przetarg?</DialogTitle>
            <DialogDescription>
              {rejectedTender?.tender_name}
            </DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="Np. nie pasuje do naszej branży, za krótki termin..."
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            rows={3}
          />
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="ghost" onClick={dismissRejectDialog}>
              Pomiń
            </Button>
            <Button
              onClick={handleSendFeedback}
              disabled={!feedbackText.trim() || isSendingFeedback}
            >
              {isSendingFeedback ? "Wysyłanie..." : "Wyślij"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
