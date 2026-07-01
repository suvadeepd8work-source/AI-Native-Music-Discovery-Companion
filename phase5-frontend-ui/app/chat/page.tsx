"use client"

import { useState } from "react"
import { apiClient, ChatResponse } from "@/lib/api"
import { Send } from "lucide-react"
import { RecommendationCard } from "@/components/recommendation-card"
import { InlineLoading } from "@/components/loading-spinner"
import { ErrorAlert } from "@/components/error-boundary"

export default function Chat() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [conversationHistory, setConversationHistory] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.chat({
        user_id: "user_1",
        session_id: "session_1",
        query,
        conversation_history: conversationHistory,
        enable_recommendations: true,
        enable_explanations: true,
        enable_review_insights: true,
        max_recommendations: 10,
      })
      setResponse(result)
      setConversationHistory([
        ...conversationHistory,
        { role: "user", content: query },
        { role: "assistant", content: result.response },
      ])
      setQuery("")
    } catch (error) {
      console.error("Chat error:", error)
      setError("Failed to send message. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 md:p-8 h-full flex flex-col">
      <div className="max-w-5xl mx-auto w-full flex-1 flex flex-col">
        <h1 className="text-3xl font-bold mb-6">AI Chat</h1>
        
        <div className="flex-1 p-6 bg-card border border-border rounded-lg flex flex-col min-h-0">
          <h2 className="text-lg font-semibold mb-4">Conversation</h2>
          <div className="flex-1 space-y-4 overflow-y-auto mb-4 min-h-0">
            {conversationHistory.map((msg, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground ml-auto max-w-[80%]"
                    : "bg-muted text-muted-foreground mr-auto max-w-[80%]"
                }`}
              >
                {msg.content}
              </div>
            ))}
            {response && !conversationHistory.length && (
              <div className="p-4 rounded-lg bg-muted text-muted-foreground">
                {response.response}
              </div>
            )}
            {loading && (
              <div className="flex justify-center">
                <InlineLoading text="Thinking..." />
              </div>
            )}
          </div>

          {error && (
            <div className="mb-4">
              <ErrorAlert message={error} onRetry={() => handleSubmit(new Event("submit") as any)} />
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2 mt-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about music discovery..."
            className="flex-1 px-4 py-3 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <InlineLoading text="Sending..." />
            ) : (
              <>
                <Send className="h-4 w-4" />
                Send
              </>
            )}
          </button>
        </form>

        {response && response.recommendations && response.recommendations.length > 0 && (
          <div className="mt-6 p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Recommendations</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {response.recommendations.map((rec, index) => (
                <RecommendationCard
                  key={index}
                  track={rec.track}
                  confidence={rec.confidence}
                  explanation={rec.explanation}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
