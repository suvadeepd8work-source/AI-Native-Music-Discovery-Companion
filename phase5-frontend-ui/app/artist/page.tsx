"use client"

import { useState } from "react"
import { apiClient, SimilarArtistsResponse } from "@/lib/api"
import { Search } from "lucide-react"
import { ArtistCard } from "@/components/artist-card"
import { PageLoading, InlineLoading } from "@/components/loading-spinner"
import { ErrorAlert } from "@/components/error-boundary"

export default function Artist() {
  const [artistName, setArtistName] = useState("")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SimilarArtistsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!artistName.trim()) return

    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.getSimilarArtists({
        artist_name: artistName,
        limit: 10,
      })
      setResults(result)
    } catch (error) {
      console.error("Artist search error:", error)
      setError("Failed to find similar artists. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Artist Information</h1>
        
        <div className="mb-8 p-6 bg-card border border-border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Find Similar Artists</h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={artistName}
              onChange={(e) => setArtistName(e.target.value)}
              placeholder="Enter artist name (e.g., Daft Punk)"
              className="flex-1 px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !artistName.trim()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <InlineLoading text="Searching..." />
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Search
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="mt-4">
              <ErrorAlert message={error} onRetry={handleSearch} />
            </div>
          )}
        </div>

        {loading && <PageLoading />}

        {results && results.success && (
          <div className="space-y-6">
            <div className="p-6 bg-card border border-border rounded-lg">
              <h2 className="text-lg font-semibold mb-4">Similar Artists</h2>
              <div className="mb-4">
                <span className="text-sm text-muted-foreground">
                  Found {results.similar_artists.length} similar artists
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {results.similar_artists.map((artist, index) => (
                  <ArtistCard
                    key={index}
                    artist={artist}
                    similarity={artist.similarity_score}
                  />
                ))}
              </div>
            </div>

            {results.discovery_context && (
              <div className="p-6 bg-card border border-border rounded-lg">
                <h2 className="text-lg font-semibold mb-4">Discovery Context</h2>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <p><strong>Strategy:</strong> {results.discovery_context.strategy}</p>
                  <p><strong>Source:</strong> {results.discovery_context.source}</p>
                  <p><strong>Confidence:</strong> {(results.discovery_context.confidence * 100).toFixed(0)}%</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
