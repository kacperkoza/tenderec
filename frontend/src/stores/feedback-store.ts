import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { FeedbackType, TenderFeedback } from "@/types/api";

interface FeedbackState {
  /** Map of tender_url -> feedback */
  feedbacks: Record<string, TenderFeedback>;
  setFeedback: (tenderUrl: string, feedback: FeedbackType) => void;
  getFeedback: (tenderUrl: string) => FeedbackType;
  clearAll: () => void;
}

export const useFeedbackStore = create<FeedbackState>()(
  persist(
    (set, get) => ({
      feedbacks: {},

      setFeedback: (tenderUrl, feedback) =>
        set((state) => ({
          feedbacks: {
            ...state.feedbacks,
            [tenderUrl]: {
              tender_url: tenderUrl,
              feedback,
              timestamp: Date.now(),
            },
          },
        })),

      getFeedback: (tenderUrl) => get().feedbacks[tenderUrl]?.feedback ?? null,

      clearAll: () => set({ feedbacks: {} }),
    }),
    { name: "tenderec-feedback" }
  )
);

