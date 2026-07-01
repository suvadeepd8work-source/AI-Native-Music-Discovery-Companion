"use client"

import { useState } from "react"
import { Settings as SettingsIcon, Save } from "lucide-react"

export default function Settings() {
  const [settings, setSettings] = useState({
    enableRecommendations: true,
    enableExplanations: true,
    enableReviewInsights: true,
    maxRecommendations: 10,
    discoveryPreference: "balanced",
    theme: "light",
  })

  const handleSave = () => {
    console.log("Saving settings:", settings)
    // In a real app, this would save to localStorage or API
  }

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Settings</h1>
        
        <div className="space-y-6">
          <div className="p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Recommendation Settings</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Enable Recommendations</div>
                  <div className="text-sm text-muted-foreground">
                    Show music recommendations in chat
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.enableRecommendations}
                  onChange={(e) => setSettings({ ...settings, enableRecommendations: e.target.checked })}
                  className="w-5 h-5"
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Enable Explanations</div>
                  <div className="text-sm text-muted-foreground">
                    Show detailed explanations for recommendations
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.enableExplanations}
                  onChange={(e) => setSettings({ ...settings, enableExplanations: e.target.checked })}
                  className="w-5 h-5"
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Enable Review Insights</div>
                  <div className="text-sm text-muted-foreground">
                    Use review-based discovery for recommendations
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.enableReviewInsights}
                  onChange={(e) => setSettings({ ...settings, enableReviewInsights: e.target.checked })}
                  className="w-5 h-5"
                />
              </div>
              <div>
                <label className="block font-medium mb-2">Max Recommendations</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={settings.maxRecommendations}
                  onChange={(e) => setSettings({ ...settings, maxRecommendations: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block font-medium mb-2">Discovery Preference</label>
                <select
                  value={settings.discoveryPreference}
                  onChange={(e) => setSettings({ ...settings, discoveryPreference: e.target.value })}
                  className="w-full px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="novel">Novel (Discover new music)</option>
                  <option value="balanced">Balanced (Mix of new and familiar)</option>
                  <option value="familiar">Familiar (Stay in comfort zone)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Appearance</h2>
            <div className="space-y-4">
              <div>
                <label className="block font-medium mb-2">Theme</label>
                <select
                  value={settings.theme}
                  onChange={(e) => setSettings({ ...settings, theme: e.target.value })}
                  className="w-full px-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
                </select>
              </div>
            </div>
          </div>

          <div className="p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">API Configuration</h2>
            <div className="space-y-4">
              <div>
                <label className="block font-medium mb-2">API URL</label>
                <input
                  type="text"
                  value={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005"}
                  disabled
                  className="w-full px-4 py-2 bg-muted border border-border rounded-md text-muted-foreground"
                />
                <div className="text-xs text-muted-foreground mt-1">
                  Configured via environment variable
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleSave}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
