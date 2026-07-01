const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005'

export interface ChatResponse {
  response: string
  intent?: string
  recommendations?: any[]
  success: boolean
}

export interface DiscoverMusicResponse {
  recommendations: any[]
  strategies_used: string[]
  total_count: number
  success: boolean
}

export interface ExplainRecommendationResponse {
  recommendation_id: string
  song_selection_reasons: string[]
  artist_selection_reasons: string[]
  user_preference_influences: string[]
  conversation_context_influences: string[]
  discovery_benefits: string[]
  scores: Record<string, number>
  success: boolean
}

export interface RecommendationHistoryResponse {
  user_id: string
  history: any[]
  total_count: number
  success: boolean
}

export interface TrendingGenresResponse {
  genres: any[]
  total_count: number
  success: boolean
}

export interface SimilarArtistsResponse {
  artist_id: string
  similar_artists: any[]
  total_count: number
  success: boolean
}

export interface DiscoveryInsightsResponse {
  user_id: string
  pain_points: any[]
  theme_clusters: any[]
  user_segments: any[]
  product_insights: any[]
  executive_summary?: string
  success: boolean
}

export interface ConversationHistoryResponse {
  user_id: string
  session_id?: string
  history: any[]
  total_count: number
  success: boolean
}

export interface HealthCheckResponse {
  status: string
  services: Record<string, string>
  version: string
  timestamp: string
}

class APIClient {
  private baseUrl: string

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`)
    }

    return response.json()
  }

  // Chat
  async chat(data: {
    user_id: string
    session_id: string
    query: string
    conversation_history?: any[]
    enable_recommendations?: boolean
    enable_explanations?: boolean
    enable_review_insights?: boolean
    max_recommendations?: number
  }): Promise<ChatResponse> {
    return this.request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Discover Music
  async discoverMusic(data: {
    user_id: string
    session_id: string
    mood?: string
    activity?: string
    genres?: string[]
    artists?: string[]
    discovery_preference?: string
    limit?: number
  }): Promise<DiscoverMusicResponse> {
    return this.request<DiscoverMusicResponse>('/api/discover', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Explain Recommendation
  async explainRecommendation(data: {
    user_id: string
    recommendation_id: string
  }): Promise<ExplainRecommendationResponse> {
    return this.request<ExplainRecommendationResponse>('/api/explain', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Recommendation History
  async getRecommendationHistory(params: {
    user_id: string
    limit?: number
  }): Promise<RecommendationHistoryResponse> {
    const queryString = new URLSearchParams(params as any).toString()
    return this.request<RecommendationHistoryResponse>(
      `/api/recommendations/history?${queryString}`
    )
  }

  // Trending Genres
  async getTrendingGenres(params: { limit?: number } = {}): Promise<TrendingGenresResponse> {
    const queryString = new URLSearchParams(params as any).toString()
    return this.request<TrendingGenresResponse>(
      `/api/trending/genres?${queryString}`
    )
  }

  // Similar Artists
  async getSimilarArtists(params: {
    artist_id: string
    limit?: number
  }): Promise<SimilarArtistsResponse> {
    const queryString = new URLSearchParams(params as any).toString()
    return this.request<SimilarArtistsResponse>(
      `/api/artists/similar?${queryString}`
    )
  }

  // Discovery Insights
  async getDiscoveryInsights(params: {
    user_id: string
    insight_type?: string
  }): Promise<DiscoveryInsightsResponse> {
    const queryString = new URLSearchParams(params as any).toString()
    return this.request<DiscoveryInsightsResponse>(
      `/api/insights/discovery?${queryString}`
    )
  }

  // Conversation History
  async getConversationHistory(params: {
    user_id: string
    session_id?: string
    limit?: number
  }): Promise<ConversationHistoryResponse> {
    const queryString = new URLSearchParams(params as any).toString()
    return this.request<ConversationHistoryResponse>(
      `/api/conversation/history?${queryString}`
    )
  }

  // Health Check
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>('/health')
  }
}

export const apiClient = new APIClient()
