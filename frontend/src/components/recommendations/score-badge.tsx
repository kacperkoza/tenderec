"use client";

import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number;
}

export function ScoreBadge({ score }: ScoreBadgeProps) {
  const percentage = Math.round(score * 100);

  const colorClass =
    score >= 0.85
      ? "bg-green-100 text-green-800 border-green-300"
      : score >= 0.7
        ? "bg-yellow-100 text-yellow-800 border-yellow-300"
        : "bg-red-100 text-red-800 border-red-300";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        colorClass
      )}
    >
      {percentage}% match
    </span>
  );
}

