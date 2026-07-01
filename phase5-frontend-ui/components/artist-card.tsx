import { Play, Heart, Users, Disc } from "lucide-react"

interface ArtistCardProps {
  artist: {
    id: string
    name: string
    genres?: string[]
    popularity?: number
    followers?: number
    image_url?: string
  }
  similarity?: number
  onPlay?: () => void
  onSave?: () => void
}

export function ArtistCard({
  artist,
  similarity,
  onPlay,
  onSave,
}: ArtistCardProps) {
  return (
    <div className="group relative bg-card border border-border rounded-lg overflow-hidden hover:border-primary transition-all hover:shadow-lg">
      <div className="aspect-square bg-muted relative">
        {artist.image_url ? (
          <img
            src={artist.image_url}
            alt={artist.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/20 to-primary/5">
            <Disc className="h-16 w-16 text-primary/50" />
          </div>
        )}
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
        <h3 className="font-semibold text-foreground truncate">{artist.name}</h3>
        {artist.genres && artist.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {artist.genres.slice(0, 3).map((genre) => (
              <span
                key={genre}
                className="text-xs px-2 py-1 bg-muted text-muted-foreground rounded-full"
              >
                {genre}
              </span>
            ))}
          </div>
        )}
        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
          {artist.followers && (
            <div className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              <span>{formatFollowers(artist.followers)}</span>
            </div>
          )}
          {artist.popularity && (
            <span>Popularity: {artist.popularity}</span>
          )}
        </div>
        {similarity !== undefined && (
          <div className="mt-3 flex items-center gap-2">
            <div className="h-1.5 flex-1 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${similarity * 100}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground">
              {(similarity * 100).toFixed(0)}% similar
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function formatFollowers(count: number): string {
  if (count >= 1000000) {
    return `${(count / 1000000).toFixed(1)}M`
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`
  }
  return count.toString()
}
