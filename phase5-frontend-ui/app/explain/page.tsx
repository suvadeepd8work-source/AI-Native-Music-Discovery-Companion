"use client"

import { useState } from "react"
import { apiClient, ExplainRecommendationResponse } from "@/lib/api"
import { Lightbulb } from "lucide-react"
import { ExplanationCard } from "@/components/explanation-card"
import { InlineLoading, PageLoading } from "@/components/loading-spinner"
import { ErrorAlert } from "@/components/error-boundary"

export default function Explain() {
  const [recommendationId, setRecommendationId] = useState("")
  const [loading, setLoading] = useState(false)
  const [explanation, setExplanation] = useState<ExplainRecommendationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleExplain = async () => {
    if (!recommendationId.trim()) return

    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.explainRecommendation({
        user_id: "user_1",
        recommendation_id: recommendationId,
      })
      setExplanation(result)
    } catch (error) {
      console.error("Explain error:", error)
      setError("Failed to get explanation. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
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
                <InlineLoading text="Explaining..." />
              ) : (
                <>
                  <Lightbulb className="h-4 w-4" />
                  Explain
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="mt-4">
              <ErrorAlert message={error} onRetry={handleExplain} />
            </div>
          )}
        </div>

        {loading && <PageLoading />}

        {explanation && explanation.success && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ExplanationCard
              title="Song Selection Reasons"
              icon="lightbulb"
              items={explanation.song_selection_reasons}
            />
            <ExplanationCard
              title="Artist Selection Reasons"
              icon="trending"
              items={explanation.artist_selection_reasons}
            />
            <ExplanationCard
              title="User Preference Influences"
              icon="target"
              items={explanation.user_preference_influences}
            />
            <ExplanationCard
              title="Conversation Context Influences"
              icon="message"
              items={explanation.conversation_context_influences}
            />
            <ExplanationCard
              title="Discovery Benefits"
              icon="sparkles"
              items={explanation.discovery_benefits}
            />
            <ExplanationCard
              title="Scoring Factors"
              icon="lightbulb"
              items={[]}
              scores={explanation.scores}
            />
          </div>
        )}
      </div>
    </div>
  )
}
