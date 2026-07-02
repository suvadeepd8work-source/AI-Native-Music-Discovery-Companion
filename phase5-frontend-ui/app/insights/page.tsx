"use client"

import { useState, useEffect } from "react"
import { apiClient, DiscoveryInsightsResponse } from "@/lib/api"
import { BarChart3 } from "lucide-react"
import { PageLoading } from "@/components/loading-spinner"
import { ErrorAlert } from "@/components/error-boundary"

export default function Insights() {
  const [loading, setLoading] = useState(true)
  const [insights, setInsights] = useState<DiscoveryInsightsResponse | null>(null)
  const [insightType, setInsightType] = useState<string>("all")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchInsights()
  }, [insightType])

  const fetchInsights = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.getDiscoveryInsights({
        user_id: "user_1",
        insight_type: insightType === "all" ? undefined : insightType,
      })
      setInsights(result)
    } catch (error) {
      console.error("Insights error:", error)
      setError("Failed to load insights. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <PageLoading />
  }

  return (
    <div className="p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Discovery Insights</h1>
        
        {error && (
          <div className="mb-6">
            <ErrorAlert message={error} onRetry={fetchInsights} />
          </div>
        )}

        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setInsightType("all")}
              className={`px-4 py-2 rounded-md transition-colors ${
                insightType === "all"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setInsightType("pain_points")}
              className={`px-4 py-2 rounded-md transition-colors ${
                insightType === "pain_points"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Pain Points
            </button>
            <button
              onClick={() => setInsightType("themes")}
              className={`px-4 py-2 rounded-md transition-colors ${
                insightType === "themes"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Themes
            </button>
            <button
              onClick={() => setInsightType("segments")}
              className={`px-4 py-2 rounded-md transition-colors ${
                insightType === "segments"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Segments
            </button>
          </div>
        </div>

        {insights && insights.success ? (
          <div className="space-y-6">
            {insights.executive_summary && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Executive Summary
                </h2>
                <p className="text-muted-foreground">{insights.executive_summary}</p>
              </div>
            )}

            {insights.pain_points && insights.pain_points.length > 0 && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">Pain Points</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {insights.pain_points.map((point, index) => (
                    <div key={index} className="p-4 bg-muted rounded-md hover:bg-muted/80 transition-colors">
                      <div className="font-medium">{point.description}</div>
                      <div className="text-sm text-muted-foreground mt-2">
                        <div>Severity: {(point.severity * 100).toFixed(0)}%</div>
                        <div>Frequency: {point.frequency}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights.theme_clusters && insights.theme_clusters.length > 0 && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">Theme Clusters</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {insights.theme_clusters.map((cluster, index) => (
                    <div key={index} className="p-4 bg-muted rounded-md hover:bg-muted/80 transition-colors">
                      <div className="font-medium">{cluster.theme_name}</div>
                      <div className="text-sm text-muted-foreground mt-2">
                        <div>Sentiment: {cluster.sentiment.toFixed(2)}</div>
                        <div>Frequency: {cluster.frequency}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights.user_segments && insights.user_segments.length > 0 && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">User Segments</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {insights.user_segments.map((segment, index) => (
                    <div key={index} className="p-4 bg-muted rounded-md hover:bg-muted/80 transition-colors">
                      <div className="font-medium">{segment.segment_name}</div>
                      <div className="text-sm text-muted-foreground mt-2">
                        Size: {segment.size.toLocaleString()} users
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights.product_insights && insights.product_insights.length > 0 && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">Product Insights</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {insights.product_insights.map((insight, index) => (
                    <div key={index} className="p-4 bg-muted rounded-md hover:bg-muted/80 transition-colors">
                      <div className="font-medium">{insight.title}</div>
                      <div className="text-sm text-muted-foreground mt-2">
                        <div>Category: {insight.category}</div>
                        <div>Impact: {insight.impact}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 bg-card border border-border rounded-lg">
            <p className="text-muted-foreground">No insights found</p>
          </div>
        )}
      </div>
    </div>
  )
}
