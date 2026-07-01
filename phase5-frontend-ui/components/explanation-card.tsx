import { Lightbulb, TrendingUp, Target, MessageSquare, Sparkles } from "lucide-react"

interface ExplanationCardProps {
  title: string
  icon: "lightbulb" | "trending" | "target" | "message" | "sparkles"
  items: string[]
  scores?: Record<string, number>
}

export function ExplanationCard({ title, icon, items, scores }: ExplanationCardProps) {
  const IconComponent = {
    lightbulb: Lightbulb,
    trending: TrendingUp,
    target: Target,
    message: MessageSquare,
    sparkles: Sparkles,
  }[icon]

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-primary/10 rounded-lg">
          <IconComponent className="h-5 w-5 text-primary" />
        </div>
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
            <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
      {scores && (
        <div className="mt-4 pt-4 border-t border-border">
          <h4 className="text-sm font-medium mb-3">Scoring Factors</h4>
          <div className="space-y-2">
            {Object.entries(scores).map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground flex-1 capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                <div className="h-2 w-24 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground w-12 text-right">
                  {(value * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
