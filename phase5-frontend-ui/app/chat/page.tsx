"use client"

import { useState } from "react"
import { apiClient, ChatResponse } from "@/lib/api"
import { Send, Loader2 } from "lucide-react"

export default function Chat() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [conversationHistory, setConversationHistory] = useState<any[]>([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    setLoading(true)
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
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">AI Chat</h1>
        
        <div className="mb-6 p-6 bg-card border border-border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Conversation</h2>
          <div className="space-y-4 max-h-96 overflow-y-auto mb-4">
            {conversationHistory.map((msg, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground ml-auto max-w-[80%]"
                    : "bg-muted text-muted-foreground mr-auto max-w-[80%]"
                }`}
              >
                {msg.content}
              </div>
            ))}
            {response && !conversationHistory.length && (
              <div className="p-3 rounded-lg bg-muted text-muted-foreground">
                {response.response}
              </div>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about music discovery..."
            className="flex-1 px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            Send
          </button>
        </form>

        {response && response.recommendations && response.recommendations.length > 0 && (
          <div className="mt-6 p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Recommendations</h2>
            <div className="space-y-3">
              {response.recommendations.map((rec, index) => (
                <div key={index} className="p-3 bg-muted rounded-md">
                  <div className="font-medium">{rec.track?.name}</div>
                  <div className="text-sm text-muted-foreground">{rec.track?.artist_name}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
