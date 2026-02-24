"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface ThresholdSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export function ThresholdSlider({ value, onChange }: ThresholdSliderProps) {
  const [local, setLocal] = useState(value);

  return (
    <div className="flex items-center gap-4">
      <label className="text-sm font-medium whitespace-nowrap">
        Min. match: {Math.round(local * 100)}%
      </label>
      <input
        type="range"
        min={0}
        max={100}
        step={5}
        value={Math.round(local * 100)}
        onChange={(e) => setLocal(Number(e.target.value) / 100)}
        className="w-40 accent-primary"
      />
      <Button
        size="sm"
        variant="outline"
        onClick={() => onChange(local)}
        disabled={local === value}
      >
        Apply
      </Button>
    </div>
  );
}

