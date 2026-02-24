import { API_BASE_URL } from "./constants";
import type { RecommendationsResponse } from "@/types/api";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }

    return res.json() as Promise<T>;
  }

  async getRecommendations(
    companyId: string,
    threshold?: number
  ): Promise<RecommendationsResponse> {
    const params = threshold != null ? `?threshold=${threshold}` : "";
    return this.request<RecommendationsResponse>(
      `/classify/recommendations/${companyId}${params}`
    );
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

