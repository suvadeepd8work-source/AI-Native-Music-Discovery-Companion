"use client"

import { useState, useEffect } from "react"
import { apiClient, ConversationHistoryResponse } from "@/lib/api"
import { PageLoading } from "@/components/loading-spinner"
import { ErrorAlert } from "@/components/error-boundary"

export default function History() {
  const [loading, setLoading] = useState(true)
  const [history, setHistory] = useState<ConversationHistoryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiClient.getConversationHistory({ user_id: "user_1", limit: 50 })
      .then(setHistory)
      .catch((err) => {
        console.error("History error:", err)
        setError("Failed to load conversation history. Please try again.")
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <PageLoading />
  }

  return (
    <div className="p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Conversation History</h1>
        
        {error && (
          <div className="mb-6">
            <ErrorAlert message={error} onRetry={() => window.location.reload()} />
          </div>
        )}

        {history && history.success ? (
          <div className="p-6 bg-card border border-border rounded-lg">
            <div className="mb-4">
              <span className="text-sm text-muted-foreground">
                Total conversations: {history.total_count}
              </span>
            </div>
            <div className="space-y-4">
              {history.history.map((item, index) => (
                <div key={index} className="p-4 bg-muted rounded-md hover:bg-muted/80 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="font-medium text-foreground mb-2">{item.query}</div>
                      <div className="text-sm text-muted-foreground">{item.response}</div>
                    </div>
                    <div className="flex-shrink-0 text-xs text-muted-foreground whitespace-nowrap">
                      {item.intent && <div className="mb-1">Intent: {item.intent}</div>}
                      {item.timestamp && <div>{new Date(item.timestamp).toLocaleString()}</div>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-6 bg-card border border-border rounded-lg">
            <p className="text-muted-foreground">No conversation history found</p>
          </div>
        )}
      </div>
    </div>
  )
}
