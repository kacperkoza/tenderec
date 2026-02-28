import type {
  CompanyProfile,
  CreateCompanyRequest,
  CreateFeedbackRequest,
  Feedback,
  FeedbackListResponse,
  RecommendationsParams,
  RecommendationsResponse,
  TenderDetails,
  TenderQuestionRequest,
  TenderQuestionResponse,
} from "@/types/api";

const API_BASE = "/api/v1";

export class NotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NotFoundError";
  }
}

export async function createCompany(
  name: string,
  data: CreateCompanyRequest
): Promise<CompanyProfile> {
  const res = await fetch(`${API_BASE}/companies/${encodeURIComponent(name)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error(`Nie udalo sie utworzyc profilu firmy: ${res.status}`);
  }

  return res.json();
}

export async function getCompany(name: string): Promise<CompanyProfile> {
  const res = await fetch(`${API_BASE}/companies/${encodeURIComponent(name)}`);

  if (res.status === 404) {
    throw new NotFoundError("Profil firmy nie zostal znaleziony");
  }

  if (!res.ok) {
    throw new Error(`Nie udalo sie pobrac profilu firmy: ${res.status}`);
  }

  return res.json();
}

export async function getRecommendations(
  params: RecommendationsParams
): Promise<RecommendationsResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set("company", params.company);
  if (params.name_match) searchParams.set("name_match", params.name_match);
  if (params.industry_match)
    searchParams.set("industry_match", params.industry_match);

  const res = await fetch(
    `${API_BASE}/tenders/recommendations?${searchParams.toString()}`
  );

  if (!res.ok) {
    throw new Error(`Nie udalo sie pobrac rekomendacji: ${res.status}`);
  }

  return res.json();
}

export async function getFeedbacks(
  company: string
): Promise<FeedbackListResponse> {
  const res = await fetch(
    `${API_BASE}/feedback/${encodeURIComponent(company)}`
  );

  if (!res.ok) {
    throw new Error(`Nie udalo sie pobrac opinii: ${res.status}`);
  }

  return res.json();
}

export async function createFeedback(
  company: string,
  data: CreateFeedbackRequest
): Promise<Feedback> {
  const res = await fetch(
    `${API_BASE}/feedback/${encodeURIComponent(company)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }
  );

  if (!res.ok) {
    throw new Error(`Nie udalo sie dodac opinii: ${res.status}`);
  }

  return res.json();
}

export async function getTender(name: string): Promise<TenderDetails> {
  const res = await fetch(
    `${API_BASE}/tenders/${encodeURIComponent(name)}`
  );

  if (res.status === 404) {
    throw new NotFoundError("Przetarg nie zostal znaleziony");
  }

  if (!res.ok) {
    throw new Error(`Nie udalo sie pobrac przetargu: ${res.status}`);
  }

  return res.json();
}

export async function askTenderQuestion(
  data: TenderQuestionRequest
): Promise<TenderQuestionResponse> {
  const res = await fetch(`${API_BASE}/tenders/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (res.status === 404) {
    throw new NotFoundError("Przetarg nie zostal znaleziony");
  }

  if (!res.ok) {
    throw new Error(`Nie udalo sie uzyskac odpowiedzi: ${res.status}`);
  }

  return res.json();
}
