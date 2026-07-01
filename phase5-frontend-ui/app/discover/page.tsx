"use client"

import { useState } from "react"
import { apiClient, DiscoverMusicResponse } from "@/lib/api"
import { Search, Loader2 } from "lucide-react"

export default function Discover() {
  const [mood, setMood] = useState("")
  const [activity, setActivity] = useState("")
  const [genres, setGenres] = useState("")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<DiscoverMusicResponse | null>(null)

  const handleDiscover = async () => {
    setLoading(true)
    try {
      const result = await apiClient.discoverMusic({
        user_id: "user_1",
        session_id: "session_1",
        mood: mood || undefined,
        activity: activity || undefined,
        genres: genres ? genres.split(",").map(g => g.trim()) : [],
        discovery_preference: "balanced",
        limit: 10,
      })
      setResults(result)
    } catch (error) {
      console.error("Discover error:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Music Discovery</h1>
        
        <div className="mb-8 p-6 bg-card border border-border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Discover New Music</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2">Mood</label>
              <input
                type="text"
                value={mood}
                onChange={(e) => setMood(e.target.value)}
                placeholder="e.g., energetic, calm, melancholic"
                className="w-full px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Activity</label>
              <input
                type="text"
                value={activity}
                onChange={(e) => setActivity(e.target.value)}
                placeholder="e.g., workout, coding, studying"
                className="w-full px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-2">Genres (comma-separated)</label>
              <input
                type="text"
                value={genres}
                onChange={(e) => setGenres(e.target.value)}
                placeholder="e.g., synthwave, lo-fi, indie pop"
                className="w-full px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <button
            onClick={handleDiscover}
            disabled={loading}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Discover Music
          </button>
        </div>

        {results && results.success && (
          <div className="p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Recommendations</h2>
            <div className="mb-4">
              <span className="text-sm text-muted-foreground">
                Strategies used: {results.strategies_used.join(", ")}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.recommendations.map((rec, index) => (
                <div key={index} className="p-4 bg-muted rounded-md">
                  <div className="font-medium">{rec.track?.name}</div>
                  <div className="text-sm text-muted-foreground">{rec.track?.artist_name}</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Confidence: {(rec.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-muted-foreground mt-2">
                    {rec.explanation}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
