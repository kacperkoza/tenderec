"use client";

import { useMemo, useState, useCallback } from "react";
import { useRecommendations } from "@/hooks/use-recommendations";
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

export default function TendersPage() {
  const { data, isLoading, error, refetch } = useRecommendations({
    company: "greenworks",
  });

  const { swipe, isSwiped, getLiked, clearAll } = useTenderSwipeStore();
  const [currentIndex, setCurrentIndex] = useState(0);

  const unswiped = useMemo(() => {
    if (!data?.recommendations) return [];
    return data.recommendations.filter((r) => !isSwiped(r.tender_name));
  }, [data, isSwiped]);

  // Reset index when unswiped list changes
  const visibleCards = unswiped.slice(0, 2);

  const handleSwipe = useCallback(
    (direction: SwipeDirection) => {
      const current = visibleCards[0];
      if (!current) return;
      swipe(current.tender_name, direction);
      setCurrentIndex((i) => i + 1);
    },
    [visibleCards, swipe]
  );

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

  return (
    <div className="mx-auto max-w-md space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Rekomendowane przetargi</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Przesuń w prawo aby polubić, w lewo aby odrzucić
        </p>
      </div>

      {allDone ? (
        <Card>
          <CardHeader>
            <CardTitle>To już wszystko!</CardTitle>
            <CardDescription>
              Przejrzano wszystkie rekomendacje.
              {liked.length > 0 && (
                <span>
                  {" "}
                  Polubiono {liked.length}{" "}
                  {liked.length === 1
                    ? "przetarg"
                    : liked.length < 5
                      ? "przetargi"
                      : "przetargów"}
                  .
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                clearAll();
                setCurrentIndex(0);
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

      {liked.length > 0 && !allDone && (
        <div className="border-t pt-4">
          <h2 className="mb-2 text-sm font-medium text-muted-foreground">
            Polubione ({liked.length})
          </h2>
          <ul className="space-y-1">
            {liked.map((item) => (
              <li key={item.tender_name} className="text-sm">
                {item.tender_name}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
