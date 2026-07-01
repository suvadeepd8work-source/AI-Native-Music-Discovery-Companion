import { Play, Heart, MoreHorizontal } from "lucide-react"

interface RecommendationCardProps {
  track: {
    name: string
    artist_name: string
    album_name?: string
    duration_ms?: number
    popularity?: number
  }
  confidence: number
  explanation?: string
  onPlay?: () => void
  onSave?: () => void
}

export function RecommendationCard({
  track,
  confidence,
  explanation,
  onPlay,
  onSave,
}: RecommendationCardProps) {
  return (
    <div className="group relative bg-card border border-border rounded-lg overflow-hidden hover:border-primary transition-all hover:shadow-lg">
      <div className="aspect-square bg-muted relative">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
            <Play className="h-8 w-8 text-primary" />
          </div>
        </div>
        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
          <button
            onClick={onPlay}
            className="p-3 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 transition-colors"
          >
            <Play className="h-5 w-5" />
          </button>
          <button
            onClick={onSave}
            className="p-3 bg-background text-foreground rounded-full hover:bg-accent transition-colors"
          >
            <Heart className="h-5 w-5" />
          </button>
        </div>
      </div>
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-foreground truncate">{track.name}</h3>
            <p className="text-sm text-muted-foreground truncate">{track.artist_name}</p>
            {track.album_name && (
              <p className="text-xs text-muted-foreground truncate">{track.album_name}</p>
            )}
          </div>
          <button className="p-1 hover:bg-accent rounded-md transition-colors">
            <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-1.5 flex-1 bg-muted rounded-full overflow-hidden max-w-24">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground">
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
          {track.duration_ms && (
            <span className="text-xs text-muted-foreground">
              {Math.floor(track.duration_ms / 60000)}:{String(
                Math.floor((track.duration_ms % 60000) / 1000)
              ).padStart(2, "0")}
            </span>
          )}
        </div>
        {explanation && (
          <p className="mt-3 text-xs text-muted-foreground line-clamp-2">
            {explanation}
          </p>
        )}
      </div>
    </div>
  )
}
