import { Play, Heart, MoreHorizontal, MessageSquare, Star, Pause } from "lucide-react"
import { useState } from "react"

interface RecommendationCardProps {
  track: {
    name: string
    artist_name: string
    album_name?: string
    duration_ms?: number
    popularity?: number
    album_art_url?: string
    audio_preview_url?: string
  }
  confidence: number
  explanation?: string
  community_reviews?: any[]
  onPlay?: () => void
  onSave?: () => void
}

export function RecommendationCard({
  track,
  confidence,
  explanation,
  community_reviews,
  onPlay,
  onSave,
}: RecommendationCardProps) {
  const [imageError, setImageError] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [showReviews, setShowReviews] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)

  const handleImageError = () => {
    setImageError(true)
  }

  const handleImageLoad = () => {
    setImageLoaded(true)
  }

  const togglePlay = () => {
    setIsPlaying(!isPlaying)
    onPlay?.()
  }

  return (
    <div className="group relative bg-[#282828] border border-[#404040] rounded-lg overflow-hidden hover:border-[#1DB954] transition-all hover:shadow-2xl hover:shadow-[#1DB954]/20">
      <div className="aspect-square bg-[#181818] relative">
        {track.album_art_url && !imageError ? (
          <>
            <img
              src={track.album_art_url}
              alt={track.album_name || track.name}
              className="w-full h-full object-cover"
              onError={handleImageError}
              onLoad={handleImageLoad}
              style={{ display: imageLoaded ? 'block' : 'none' }}
            />
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-[#1a1a2e] to-[#16213e]">
                <div className="w-16 h-16 bg-[#1DB954]/20 rounded-full flex items-center justify-center">
                  <Play className="h-8 w-8 text-[#1DB954]" />
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#1a1a2e] to-[#16213e]">
            <div className="w-16 h-16 bg-[#1DB954]/20 rounded-full flex items-center justify-center">
              <Play className="h-8 w-8 text-[#1DB954]" />
            </div>
          </div>
        )}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
          <button
            onClick={togglePlay}
            className="p-4 bg-[#1DB954] text-white rounded-full hover:bg-[#1ed760] transition-all transform hover:scale-110 shadow-lg"
          >
            {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6" />}
          </button>
          <button
            onClick={onSave}
            className="p-4 bg-white/20 backdrop-blur-sm text-white rounded-full hover:bg-white/30 transition-all transform hover:scale-110"
          >
            <Heart className="h-6 w-6" />
          </button>
        </div>
      </div>
      {track.audio_preview_url && isPlaying && (
        <div className="bg-[#181818] p-3">
          <audio
            src={track.audio_preview_url}
            autoPlay
            onEnded={() => setIsPlaying(false)}
            controls
            className="w-full h-8"
          />
        </div>
      )}
      <div className="p-4 bg-[#282828]">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-white truncate text-lg">{track.name}</h3>
            <p className="text-sm text-gray-400 truncate font-medium">{track.artist_name}</p>
            {track.album_name && (
              <p className="text-xs text-gray-500 truncate">{track.album_name}</p>
            )}
          </div>
          <button className="p-2 hover:bg-[#404040] rounded-full transition-colors">
            <MoreHorizontal className="h-5 w-5 text-gray-400" />
          </button>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2 flex-1 bg-[#404040] rounded-full overflow-hidden max-w-28">
              <div
                className="h-full bg-[#1DB954] rounded-full transition-all"
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
            <span className="text-xs text-[#1DB954] font-semibold">
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
          {track.duration_ms && (
            <span className="text-xs text-gray-400 font-medium">
              {Math.floor(track.duration_ms / 60000)}:{String(
                Math.floor((track.duration_ms % 60000) / 1000)
              ).padStart(2, "0")}
            </span>
          )}
        </div>
        {explanation && (
          <div className="mt-4 p-3 bg-[#404040] rounded-lg">
            <p className="text-xs text-gray-300 line-clamp-3 leading-relaxed">
              <span className="text-[#1DB954] font-semibold">AI says:</span> {explanation}
            </p>
          </div>
        )}
        {community_reviews && community_reviews.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowReviews(!showReviews)}
              className="flex items-center gap-2 text-xs text-[#1DB954] hover:text-[#1ed760] transition-colors"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Community Reviews ({community_reviews.length})</span>
            </button>
            {showReviews && (
              <div className="mt-3 space-y-2">
                {community_reviews.map((review, index) => (
                  <div key={index} className="p-2 bg-[#404040] rounded-lg">
                    <div className="flex items-center gap-1 mb-1">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`h-3 w-3 ${
                            i < (review.rating || 4) ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'
                          }`}
                        />
                      ))}
                    </div>
                    <p className="text-xs text-gray-300 line-clamp-2">{review.text || "Great song!"}</p>
                    <p className="text-xs text-gray-500 mt-1">{review.author || "Anonymous"}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
