"use client"

import { useState, useEffect } from "react"
import { apiClient, RecommendationHistoryResponse } from "@/lib/api"
import { Loader2 } from "lucide-react"

export default function Recommendations() {
  const [loading, setLoading] = useState(true)
  const [history, setHistory] = useState<RecommendationHistoryResponse | null>(null)

  useEffect(() => {
    apiClient.getRecommendationHistory({ user_id: "user_1", limit: 50 })
      .then(setHistory)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Recommendation History</h1>
        
        {history && history.success ? (
          <div className="p-6 bg-card border border-border rounded-lg">
            <div className="mb-4">
              <span className="text-sm text-muted-foreground">
                Total recommendations: {history.total_count}
              </span>
            </div>
            <div className="space-y-3">
              {history.history.map((item, index) => (
                <div key={index} className="p-4 bg-muted rounded-md">
                  <div className="font-medium">{item.track?.name}</div>
                  <div className="text-sm text-muted-foreground">{item.track?.artist_name}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Recommended: {item.recommended_at}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Confidence: {(item.confidence * 100).toFixed(0)}%
                  </div>
                </div>
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
