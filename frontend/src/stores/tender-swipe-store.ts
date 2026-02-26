import { create } from "zustand";
import { persist } from "zustand/middleware";

export type SwipeDirection = "left" | "right";

export interface SwipedTender {
  tender_name: string;
  direction: SwipeDirection;
  timestamp: number;
}

interface TenderSwipeState {
  swiped: Record<string, SwipedTender>;
  swipe: (tenderName: string, direction: SwipeDirection) => void;
  isLiked: (tenderName: string) => boolean;
  isDisliked: (tenderName: string) => boolean;
  isSwiped: (tenderName: string) => boolean;
  getLiked: () => SwipedTender[];
  clearAll: () => void;
}

export const useTenderSwipeStore = create<TenderSwipeState>()(
  persist(
    (set, get) => ({
      swiped: {},

      swipe: (tenderName, direction) =>
        set((state) => ({
          swiped: {
            ...state.swiped,
            [tenderName]: {
              tender_name: tenderName,
              direction,
              timestamp: Date.now(),
            },
          },
        })),

      isLiked: (tenderName) => get().swiped[tenderName]?.direction === "right",
      isDisliked: (tenderName) =>
        get().swiped[tenderName]?.direction === "left",
      isSwiped: (tenderName) => !!get().swiped[tenderName],

      getLiked: () =>
        Object.values(get().swiped).filter((s) => s.direction === "right"),

      clearAll: () => set({ swiped: {} }),
    }),
    { name: "tenderec-swipes" }
  )
);
