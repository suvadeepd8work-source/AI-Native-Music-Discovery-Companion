"use client"

import { useState, useEffect } from "react"
import { apiClient, DiscoveryInsightsResponse } from "@/lib/api"
import { BarChart3, Loader2 } from "lucide-react"

export default function Insights() {
  const [loading, setLoading] = useState(true)
  const [insights, setInsights] = useState<DiscoveryInsightsResponse | null>(null)
  const [insightType, setInsightType] = useState<string>("all")

  useEffect(() => {
    fetchInsights()
  }, [insightType])

  const fetchInsights = async () => {
    setLoading(true)
    try {
      const result = await apiClient.getDiscoveryInsights({
        user_id: "user_1",
        insight_type: insightType === "all" ? undefined : insightType,
      })
      setInsights(result)
    } catch (error) {
      console.error("Insights error:", error)
    } finally {
      setLoading(false)
    }
  }

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
        <h1 className="text-3xl font-bold mb-6">Discovery Insights</h1>
        
        <div className="mb-6">
          <div className="flex gap-2">
            <button
              onClick={() => setInsightType("all")}
              className={`px-4 py-2 rounded-md ${
                insightType === "all"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setInsightType("pain_points")}
              className={`px-4 py-2 rounded-md ${
                insightType === "pain_points"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Pain Points
            </button>
            <button
              onClick={() => setInsightType("themes")}
              className={`px-4 py-2 rounded-md ${
                insightType === "themes"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Themes
            </button>
            <button
              onClick={() => setInsightType("segments")}
              className={`px-4 py-2 rounded-md ${
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
                <h2 className="text-lg font-semibold mb-4">Executive Summary</h2>
                <p className="text-muted-foreground">{insights.executive_summary}</p>
              </div>
            )}

            {insights.pain_points.length > 0 && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">Pain Points</h2>
                <div className="space-y-3">
                  {insights.pain_points.map((point, index) => (
                    <div key={index} className="p-4 bg-muted rounded-md">
                      <div className="font-medium">{point.description}</div>
                      <div className="text-sm text-muted-foreground mt-1">
                        Severity: {(point.severity * 100).toFixed(0)}% • Frequency: {point.frequency}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights.theme_clusters.length > 0 && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">Theme Clusters</h2>
                <div className="space-y-3">
                  {insights.theme_clusters.map((cluster, index) => (
                    <div key={index} className="p-4 bg-muted rounded-md">
                      <div className="font-medium">{cluster.theme_name}</div>
                      <div className="text-sm text-muted-foreground mt-1">
                        Sentiment: {cluster.sentiment.toFixed(2)} • Frequency: {cluster.frequency}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights.user_segments.length > 0 && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">User Segments</h2>
                <div className="space-y-3">
                  {insights.user_segments.map((segment, index) => (
                    <div key={index} className="p-4 bg-muted rounded-md">
                      <div className="font-medium">{segment.segment_name}</div>
                      <div className="text-sm text-muted-foreground mt-1">
                        Size: {segment.size.toLocaleString()} users
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights.product_insights.length > 0 && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">Product Insights</h2>
                <div className="space-y-3">
                  {insights.product_insights.map((insight, index) => (
                    <div key={index} className="p-4 bg-muted rounded-md">
                      <div className="font-medium">{insight.title}</div>
                      <div className="text-sm text-muted-foreground mt-1">
                        Category: {insight.category} • Impact: {insight.impact}
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
