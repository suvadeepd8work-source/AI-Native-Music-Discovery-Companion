"use client"

import { useState } from "react"
import { apiClient, DiscoverMusicResponse } from "@/lib/api"
import { Search, Music, Sparkles } from "lucide-react"
import { RecommendationCard } from "@/components/recommendation-card"
import { PageLoading, InlineLoading } from "@/components/loading-spinner"
import { ErrorAlert } from "@/components/error-boundary"

export default function Home() {
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
        limit: 50,
      })
      setResults(result)
    } catch (error) {
      console.error("Discover error:", error)
      setError("Failed to discover music. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const moods = ["Energetic", "Relaxed", "Happy", "Sad", "Focused", "Romantic", "Chill", "Excited"]
  const activities = ["Workout", "Coding", "Studying", "Driving", "Partying", "Relaxing", "Sleeping", "Cooking"]
  const genreOptions = ["Rock", "Pop", "Hip Hop", "Electronic", "Jazz", "Classical", "R&B", "Country", "Indie", "Metal"]

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#121212] via-[#1a1a2e] to-[#16213e]">
      <div className="max-w-7xl mx-auto px-4 py-8 md:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Music className="h-12 w-12 text-[#1DB954]" />
            <h1 className="text-5xl font-bold text-white">AI Music Discovery</h1>
            <Sparkles className="h-12 w-12 text-[#1DB954]" />
          </div>
          <p className="text-xl text-gray-300">
            Discover your next favorite song with AI-powered recommendations
          </p>
        </div>

        {/* Discovery Form */}
        <div className="mb-8 p-8 bg-[#181818] border border-[#282828] rounded-2xl shadow-2xl">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-[#1DB954]" />
            Tell us your preferences
          </h2>
          
          {/* Mood Selection */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-300 mb-3">How are you feeling?</label>
            <div className="flex flex-wrap gap-2">
              {moods.map((m) => (
                <button
                  key={m}
                  onClick={() => setMood(m)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    mood === m
                      ? "bg-[#1DB954] text-white shadow-lg"
                      : "bg-[#282828] text-gray-300 hover:bg-[#333333]"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Activity Selection */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-300 mb-3">What are you doing?</label>
            <div className="flex flex-wrap gap-2">
              {activities.map((a) => (
                <button
                  key={a}
                  onClick={() => setActivity(a)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    activity === a
                      ? "bg-[#1DB954] text-white shadow-lg"
                      : "bg-[#282828] text-gray-300 hover:bg-[#333333]"
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>

          {/* Genre Selection */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-300 mb-3">Select genres</label>
            <div className="flex flex-wrap gap-2">
              {genreOptions.map((g) => (
                <button
                  key={g}
                  onClick={() => {
                    const currentGenres = genres ? genres.split(",").map(g => g.trim()) : []
                    if (currentGenres.includes(g)) {
                      setGenres(currentGenres.filter(gen => gen !== g).join(", "))
                    } else {
                      setGenres([...currentGenres, g].join(", "))
                    }
                  }}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    genres && genres.split(",").map(g => g.trim()).includes(g)
                      ? "bg-[#1DB954] text-white shadow-lg"
                      : "bg-[#282828] text-gray-300 hover:bg-[#333333]"
                  }`}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="mb-6">
              <ErrorAlert message={error} onRetry={handleDiscover} />
            </div>
          )}

          <button
            onClick={handleDiscover}
            disabled={loading}
            className="w-full px-8 py-4 bg-[#1DB954] text-white rounded-full font-bold text-lg hover:bg-[#1ed760] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-lg transition-all transform hover:scale-105"
          >
            {loading ? (
              <>
                <InlineLoading text="Discovering..." />
              </>
            ) : (
              <>
                <Search className="h-6 w-6" />
                Discover Music
              </>
            )}
          </button>
        </div>

        {loading && <PageLoading />}

        {/* Results */}
        {results && results.success && (
          <div className="p-8 bg-[#181818] border border-[#282828] rounded-2xl shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Music className="h-6 w-6 text-[#1DB954]" />
                Your Recommendations
              </h2>
              <span className="text-sm text-gray-400">
                {results.total_count} songs found
              </span>
            </div>
            
            <div className="mb-4 p-4 bg-[#282828] rounded-lg">
              <p className="text-sm text-gray-300">
                <span className="font-semibold text-[#1DB954]">AI Strategy:</span> {results.strategies_used.join(", ")}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {results.recommendations.map((rec, index) => (
                <RecommendationCard
                  key={index}
                  track={rec.track}
                  confidence={rec.confidence}
                  explanation={rec.explanation}
                  community_reviews={rec.community_reviews}
                  onPlay={() => console.log("Play:", rec.track.name)}
                  onSave={() => console.log("Save:", rec.track.name)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
