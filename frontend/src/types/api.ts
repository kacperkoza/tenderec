// Types matching backend Pydantic schemas

export interface TenderRecommendation {
  tender_url: string;
  name: string;
  organization: string;
  industry: string;
  score: number; // 0–1
  reasoning: string;
}

export interface RecommendationsResponse {
  company_id: string;
  company: string;
  threshold: number;
  total: number;
  recommendations: TenderRecommendation[];
}

export type FeedbackType = "relevant" | "not_relevant" | null;

export interface TenderFeedback {
  tender_url: string;
  feedback: FeedbackType;
  timestamp: number;
}

