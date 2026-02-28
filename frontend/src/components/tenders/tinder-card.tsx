"use client";

import { useRef, useState, type PointerEvent } from "react";
import type { TenderRecommendation, MatchLevel } from "@/types/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { SwipeDirection } from "@/stores/tender-swipe-store";

const SWIPE_THRESHOLD = 100;

const matchLabels: Record<MatchLevel, string> = {
  PERFECT_MATCH: "Bardzo dobre",
  PARTIAL_MATCH: "Częściowe",
  DONT_KNOW: "Niepewne",
  NO_MATCH: "Brak",
};

const matchColors: Record<MatchLevel, string> = {
  PERFECT_MATCH: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  PARTIAL_MATCH: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  DONT_KNOW: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
  NO_MATCH: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

function MatchBadge({ level, label }: { level: MatchLevel; label: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span
        className={cn(
          "inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-medium",
          matchColors[level]
        )}
      >
        {matchLabels[level]}
      </span>
    </div>
  );
}

interface TinderCardProps {
  tender: TenderRecommendation;
  onSwipe: (direction: SwipeDirection) => void;
  isTop: boolean;
}

export function TinderCard({ tender, onSwipe, isTop }: TinderCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [isExiting, setIsExiting] = useState(false);
  const startPos = useRef({ x: 0, y: 0 });
  const pointerId = useRef<number | null>(null);

  function handlePointerDown(e: PointerEvent) {
    if (!isTop || isExiting) return;
    pointerId.current = e.pointerId;
    startPos.current = { x: e.clientX, y: e.clientY };
    setIsDragging(true);
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }

  function handlePointerMove(e: PointerEvent) {
    if (!isDragging || pointerId.current !== e.pointerId) return;
    setOffset({
      x: e.clientX - startPos.current.x,
      y: e.clientY - startPos.current.y,
    });
  }

  function handlePointerUp(e: PointerEvent) {
    if (pointerId.current !== e.pointerId) return;
    setIsDragging(false);
    pointerId.current = null;

    if (Math.abs(offset.x) > SWIPE_THRESHOLD) {
      const direction: SwipeDirection = offset.x > 0 ? "right" : "left";
      animateExit(direction);
    } else {
      setOffset({ x: 0, y: 0 });
    }
  }

  function animateExit(direction: SwipeDirection) {
    setIsExiting(true);
    setOffset({
      x: direction === "right" ? 600 : -600,
      y: 0,
    });
    setTimeout(() => onSwipe(direction), 300);
  }

  const rotation = offset.x * 0.1;
  const opacity = isExiting
    ? 0
    : 1 - Math.min(Math.abs(offset.x) / 400, 0.5);

  const overlayDirection =
    Math.abs(offset.x) > 30
      ? offset.x > 0
        ? "right"
        : "left"
      : null;

  return (
    <div
      ref={cardRef}
      className={cn(
        "absolute inset-0 touch-none select-none",
        isExiting ? "transition-all duration-300 ease-out" : "",
        isDragging ? "cursor-grabbing" : isTop ? "cursor-grab" : ""
      )}
      style={{
        transform: `translate(${offset.x}px, ${offset.y}px) rotate(${rotation}deg)`,
        opacity,
        zIndex: isTop ? 10 : 1,
      }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      <Card className="h-full">
        {overlayDirection && (
          <div
            className={cn(
              "absolute inset-0 z-10 flex items-center justify-center rounded-xl text-4xl font-bold",
              overlayDirection === "right"
                ? "bg-green-500/20 text-green-600"
                : "bg-red-500/20 text-red-600"
            )}
          >
            {overlayDirection === "right" ? "TAK" : "NIE"}
          </div>
        )}

        <CardHeader>
          <CardTitle className="text-lg leading-snug">
            {tender.tender_name}
          </CardTitle>
          <p className="text-sm font-medium">{tender.organization}</p>
        </CardHeader>

        <CardContent>
          <details
            className="rounded-lg border bg-muted/40 p-3"
            open
            onPointerDown={(e) => e.stopPropagation()}
          >
            <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">
              Szczegóły dopasowania
            </summary>
            <div className="mt-3 space-y-4">
              <div className="space-y-2">
                <MatchBadge level={tender.name_match} label="Nazwa przetargu" />
                <p className="text-xs text-muted-foreground">
                  {tender.name_reason}
                </p>
              </div>
              <div className="space-y-2">
                <MatchBadge level={tender.industry_match} label="Branża zamawiającego" />
                <p className="text-xs text-muted-foreground">
                  {tender.industry_reason}
                </p>
              </div>
            </div>
          </details>
        </CardContent>
      </Card>
    </div>
  );
}

interface SwipeButtonsProps {
  onSwipe: (direction: SwipeDirection) => void;
  onSkip: () => void;
  disabled: boolean;
}

export function SwipeButtons({ onSwipe, onSkip, disabled }: SwipeButtonsProps) {
  return (
    <div className="flex items-center justify-center gap-8">
      <button
        onClick={() => onSwipe("left")}
        disabled={disabled}
        className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-red-300 text-red-500 transition-colors hover:bg-red-50 disabled:opacity-50 dark:border-red-700 dark:hover:bg-red-950"
        aria-label="Odrzuć"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <button
        onClick={onSkip}
        disabled={disabled}
        className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-yellow-300 text-yellow-500 transition-colors hover:bg-yellow-50 disabled:opacity-50 dark:border-yellow-600 dark:hover:bg-yellow-950"
        aria-label="Pomiń"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polygon points="5 4 15 12 5 20 5 4" />
          <line x1="19" y1="5" x2="19" y2="19" />
        </svg>
      </button>
      <button
        onClick={() => onSwipe("right")}
        disabled={disabled}
        className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-green-300 text-green-500 transition-colors hover:bg-green-50 disabled:opacity-50 dark:border-green-700 dark:hover:bg-green-950"
        aria-label="Polub"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
      </button>
    </div>
  );
}
