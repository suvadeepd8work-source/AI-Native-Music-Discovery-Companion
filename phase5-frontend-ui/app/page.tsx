"use client"

import { useState, useEffect } from "react"
import { apiClient, HealthCheckResponse, RecommendationHistoryResponse } from "@/lib/api"
import { Music, MessageSquare, Sparkles, ListMusic, Clock, TrendingUp } from "lucide-react"
import { RecommendationCard } from "@/components/recommendation-card"
import { PageLoading } from "@/components/loading-spinner"

export default function Home() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null)
  const [recentRecommendations, setRecentRecommendations] = useState<RecommendationHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      apiClient.healthCheck(),
      apiClient.getRecommendationHistory({ user_id: "user_1", limit: 4 })
    ]).then(([healthData, recommendationsData]) => {
      setHealth(healthData)
      setRecentRecommendations(recommendationsData)
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  const latestTimestamp = recentRecommendations?.history?.[0]?.timestamp
    ? new Date(recentRecommendations.history[0].timestamp).toLocaleString()
    : null

  return (
    <div className="p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Welcome to AI Music Discovery
          </h1>
          <p className="text-lg text-muted-foreground">
            Discover new music naturally through AI-powered conversations
          </p>
        </div>

        {loading && <PageLoading />}

        {!loading && health && (
          <div className="mb-8 p-4 bg-card border border-border rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-3 h-3 rounded-full ${health.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'}`} />
              <span className="font-medium">System Status: {health.status}</span>
            </div>
            <div className="text-sm text-muted-foreground">
              Version: {health.version}
            </div>
          </div>
        )}

        {!loading && recentRecommendations && recentRecommendations.success && (
          <div className="mb-8 p-6 bg-card border border-border rounded-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Recently Recommended Songs
              </h2>
              {latestTimestamp && (
                <div className="text-sm text-muted-foreground">
                  Latest: {latestTimestamp}
                </div>
              )}
            </div>
            {recentRecommendations.history && recentRecommendations.history.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {recentRecommendations.history.slice(0, 4).map((rec: any, index: number) => (
                  <RecommendationCard
                    key={index}
                    track={rec.track}
                    confidence={rec.confidence}
                    explanation={rec.explanation}
                  />
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No recent recommendations yet. Start discovering music!</p>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="p-6 bg-card border border-border rounded-lg hover:border-primary transition-colors cursor-pointer">
            <MessageSquare className="h-8 w-8 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">AI Chat</h3>
            <p className="text-sm text-muted-foreground">
              Have natural conversations to discover music
            </p>
          </div>

          <div className="p-6 bg-card border border-border rounded-lg hover:border-primary transition-colors cursor-pointer">
            <Music className="h-8 w-8 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Music Discovery</h3>
            <p className="text-sm text-muted-foreground">
              Explore music based on mood and preferences
            </p>
          </div>

          <div className="p-6 bg-card border border-border rounded-lg hover:border-primary transition-colors cursor-pointer">
            <ListMusic className="h-8 w-8 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Recommendations</h3>
            <p className="text-sm text-muted-foreground">
              View your personalized recommendations
            </p>
          </div>

          <div className="p-6 bg-card border border-border rounded-lg hover:border-primary transition-colors cursor-pointer">
            <Sparkles className="h-8 w-8 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Insights</h3>
            <p className="text-sm text-muted-foreground">
              Understand discovery patterns and trends
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="p-6 bg-card border border-border rounded-lg hover:border-primary transition-colors cursor-pointer">
            <TrendingUp className="h-8 w-8 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Discovery Insights</h3>
            <p className="text-sm text-muted-foreground">
              Explore pain points, theme clusters, and user segments
            </p>
          </div>

          <div className="p-6 bg-card border border-border rounded-lg hover:border-primary transition-colors cursor-pointer">
            <MessageSquare className="h-8 w-8 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">Conversation History</h3>
            <p className="text-sm text-muted-foreground">
              Review your past conversations and queries
            </p>
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-lg">
          <h2 className="text-2xl font-bold mb-4">Getting Started</h2>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                1
              </div>
              <div>
                <h3 className="font-semibold mb-1">Start a Conversation</h3>
                <p className="text-sm text-muted-foreground">
                  Go to AI Chat and tell us what kind of music you're looking for
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                2
              </div>
              <div>
                <h3 className="font-semibold mb-1">Get Recommendations</h3>
                <p className="text-sm text-muted-foreground">
                  Receive personalized music suggestions with explanations
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                3
              </div>
              <div>
                <h3 className="font-semibold mb-1">Explore & Discover</h3>
                <p className="text-sm text-muted-foreground">
                  Use Music Discovery to explore new genres and artists
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
