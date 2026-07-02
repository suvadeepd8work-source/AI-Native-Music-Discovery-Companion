"use client"

import { useState, useEffect } from "react"
import { apiClient, RecommendationHistoryResponse } from "@/lib/api"
import { PageLoading } from "@/components/loading-spinner"
import { ErrorAlert } from "@/components/error-boundary"
import { RecommendationCard } from "@/components/recommendation-card"

export default function Recommendations() {
  const [loading, setLoading] = useState(true)
  const [history, setHistory] = useState<RecommendationHistoryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiClient.getRecommendationHistory({ user_id: "user_1", limit: 50 })
      .then(setHistory)
      .catch((err) => {
        console.error("Recommendations error:", err)
        setError("Failed to load recommendations. Please try again.")
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <PageLoading />
  }

  return (
    <div className="p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Recommendation History</h1>
        
        {error && (
          <div className="mb-6">
            <ErrorAlert message={error} onRetry={() => window.location.reload()} />
          </div>
        )}

        {history && history.success ? (
          <div className="p-6 bg-card border border-border rounded-lg">
            <div className="mb-4">
              <span className="text-sm text-muted-foreground">
                Total recommendations: {history.total_count}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {history.history.map((item, index) => (
                <RecommendationCard
                  key={index}
                  track={item.track}
                  confidence={item.confidence}
                  explanation={item.explanation}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="p-6 bg-card border border-border rounded-lg">
            <p className="text-muted-foreground">No recommendations found</p>
          </div>
        )}
      </div>
    </div>
  )
}
