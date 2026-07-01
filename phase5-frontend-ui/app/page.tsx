"use client"

import { useState, useEffect } from "react"
import { apiClient, HealthCheckResponse } from "@/lib/api"
import { Music, MessageSquare, Sparkles, ListMusic } from "lucide-react"

export default function Home() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.healthCheck().then(setHealth).finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Welcome to AI Music Discovery
          </h1>
          <p className="text-lg text-muted-foreground">
            Discover new music naturally through AI-powered conversations
          </p>
        </div>

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
