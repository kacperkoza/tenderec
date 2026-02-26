export interface CompanyGeography {
  primary_country: string;
}

export interface MatchingCriteria {
  service_categories: string[];
  cpv_codes: string[];
  target_authorities: string[];
  geography: CompanyGeography;
}

export interface CompanyInfo {
  name: string;
  industries: string[];
}

export interface CompanyProfileData {
  company_info: CompanyInfo;
  matching_criteria: MatchingCriteria;
}

export interface CompanyProfile {
  company_name: string;
  profile: CompanyProfileData;
  created_at: string;
}

export interface CreateCompanyRequest {
  description: string;
}

export type MatchLevel =
  | "PERFECT_MATCH"
  | "PARTIAL_MATCH"
  | "DONT_KNOW"
  | "NO_MATCH";

export interface TenderRecommendation {
  tender_name: string;
  name_match: MatchLevel;
  name_reason: string;
  industry_match: MatchLevel;
  industry_reason: string;
}

export interface RecommendationsResponse {
  company: string;
  recommendations: TenderRecommendation[];
}

export interface RecommendationsParams {
  company: string;
  name_match?: MatchLevel;
  industry_match?: MatchLevel;
}

export interface Feedback {
  id: string;
  feedback_comment: string;
}

export interface FeedbackListResponse {
  company_name: string;
  feedbacks: Feedback[];
}

export interface CreateFeedbackRequest {
  feedback_comment: string;
}
