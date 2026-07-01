import { Smile, Zap, Heart, Coffee, Music, Moon, Sun } from "lucide-react"

interface MoodOption {
  id: string
  label: string
  icon: React.ReactNode
  color: string
}

const moods: MoodOption[] = [
  { id: "energetic", label: "Energetic", icon: <Zap className="h-5 w-5" />, color: "bg-yellow-500" },
  { id: "happy", label: "Happy", icon: <Smile className="h-5 w-5" />, color: "bg-green-500" },
  { id: "romantic", label: "Romantic", icon: <Heart className="h-5 w-5" />, color: "bg-pink-500" },
  { id: "chill", label: "Chill", icon: <Coffee className="h-5 w-5" />, color: "bg-blue-500" },
  { id: "focus", label: "Focus", icon: <Music className="h-5 w-5" />, color: "bg-purple-500" },
  { id: "relaxed", label: "Relaxed", icon: <Moon className="h-5 w-5" />, color: "bg-indigo-500" },
  { id: "upbeat", label: "Upbeat", icon: <Sun className="h-5 w-5" />, color: "bg-orange-500" },
]

interface MoodSelectorProps {
  selectedMood?: string
  onMoodSelect: (mood: string) => void
}

export function MoodSelector({ selectedMood, onMoodSelect }: MoodSelectorProps) {
  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium">How are you feeling?</label>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {moods.map((mood) => (
          <button
            key={mood.id}
            onClick={() => onMoodSelect(mood.id)}
            className={`p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2 hover:scale-105 ${
              selectedMood === mood.id
                ? "border-primary bg-primary/10"
                : "border-border hover:border-primary/50 bg-card"
            }`}
          >
            <div className={`p-2 rounded-full ${mood.color} text-white`}>
              {mood.icon}
            </div>
            <span className="text-sm font-medium">{mood.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
