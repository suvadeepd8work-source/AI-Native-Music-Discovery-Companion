"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  Home,
  MessageSquare,
  Music,
  ListMusic,
  Lightbulb,
  History,
  BarChart3,
  Settings,
} from "lucide-react"

const navigation = [
  { name: "Home", href: "/", icon: Home },
  { name: "AI Chat", href: "/chat", icon: MessageSquare },
  { name: "Music Discovery", href: "/discover", icon: Music },
  { name: "Recommendations", href: "/recommendations", icon: ListMusic },
  { name: "Explanation", href: "/explain", icon: Lightbulb },
  { name: "History", href: "/history", icon: History },
  { name: "Insights", href: "/insights", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold text-foreground">
          AI Music Discovery
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Discover music naturally
        </p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground">
          Phase 5 - Frontend UI
        </div>
      </div>
    </div>
  )
}
