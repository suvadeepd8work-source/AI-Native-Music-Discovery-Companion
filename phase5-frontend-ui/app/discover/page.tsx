"use client"

import { useState } from "react"
import { apiClient, DiscoverMusicResponse } from "@/lib/api"
import { Search } from "lucide-react"
import { MoodSelector } from "@/components/mood-selector"
import { RecommendationCard } from "@/components/recommendation-card"
import { PageLoading, InlineLoading } from "@/components/loading-spinner"
import { ErrorAlert } from "@/components/error-boundary"

export default function Discover() {
  const [mood, setMood] = useState("")
  const [activity, setActivity] = useState("")
  const [genres, setGenres] = useState("")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<DiscoverMusicResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleDiscover = async () => {
    setLoading(true)
    setError(null)
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
      setError("Failed to discover music. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Music Discovery</h1>
        
        <div className="mb-8 p-6 bg-card border border-border rounded-lg">
          <MoodSelector selectedMood={mood} onMoodSelect={setMood} />
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
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
            <div>
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

          {error && (
            <div className="mt-4">
              <ErrorAlert message={error} onRetry={handleDiscover} />
            </div>
          )}

          <button
            onClick={handleDiscover}
            disabled={loading}
            className="mt-6 w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <InlineLoading text="Discovering..." />
            ) : (
              <>
                <Search className="h-4 w-4" />
                Discover Music
              </>
            )}
          </button>
        </div>

        {loading && <PageLoading />}

        {results && results.success && (
          <div className="p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Recommendations</h2>
            <div className="mb-4">
              <span className="text-sm text-muted-foreground">
                Strategies used: {results.strategies_used.join(", ")}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {results.recommendations.map((rec, index) => (
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
