"use client"

import { useState } from "react"
import { apiClient, ExplainRecommendationResponse } from "@/lib/api"
import { Lightbulb, Loader2 } from "lucide-react"

export default function Explain() {
  const [recommendationId, setRecommendationId] = useState("")
  const [loading, setLoading] = useState(false)
  const [explanation, setExplanation] = useState<ExplainRecommendationResponse | null>(null)

  const handleExplain = async () => {
    if (!recommendationId.trim()) return

    setLoading(true)
    try {
      const result = await apiClient.explainRecommendation({
        user_id: "user_1",
        recommendation_id: recommendationId,
      })
      setExplanation(result)
    } catch (error) {
      console.error("Explain error:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Recommendation Explanation</h1>
        
        <div className="mb-8 p-6 bg-card border border-border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Get Explanation</h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={recommendationId}
              onChange={(e) => setRecommendationId(e.target.value)}
              placeholder="Enter recommendation ID"
              className="flex-1 px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={handleExplain}
              disabled={loading || !recommendationId.trim()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Lightbulb className="h-4 w-4" />
              )}
              Explain
            </button>
          </div>
        </div>

        {explanation && explanation.success && (
          <div className="space-y-6">
            <div className="p-6 bg-card border border-border rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Song Selection Reasons</h3>
              <ul className="space-y-2">
                {explanation.song_selection_reasons.map((reason, index) => (
                  <li key={index} className="text-sm text-muted-foreground">
                    • {reason}
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 bg-card border border-border rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Artist Selection Reasons</h3>
              <ul className="space-y-2">
                {explanation.artist_selection_reasons.map((reason, index) => (
                  <li key={index} className="text-sm text-muted-foreground">
                    • {reason}
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 bg-card border border-border rounded-lg">
              <h3 className="text-lg font-semibold mb-4">User Preference Influences</h3>
              <ul className="space-y-2">
                {explanation.user_preference_influences.map((influence, index) => (
                  <li key={index} className="text-sm text-muted-foreground">
                    • {influence}
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 bg-card border border-border rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Conversation Context Influences</h3>
              <ul className="space-y-2">
                {explanation.conversation_context_influences.map((influence, index) => (
                  <li key={index} className="text-sm text-muted-foreground">
                    • {influence}
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 bg-card border border-border rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Discovery Benefits</h3>
              <ul className="space-y-2">
                {explanation.discovery_benefits.map((benefit, index) => (
                  <li key={index} className="text-sm text-muted-foreground">
                    • {benefit}
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 bg-card border border-border rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Scoring Factors</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(explanation.scores).map(([key, value]) => (
                  <div key={key} className="p-3 bg-muted rounded-md">
                    <div className="text-xs text-muted-foreground">{key}</div>
                    <div className="font-medium">{(value * 100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
