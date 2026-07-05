"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Sparkles, Music, Brain, ChevronRight, X } from "lucide-react"
import { apiClient, DiscoverMusicResponse } from "@/lib/api"
import { RecommendationCard } from "@/components/recommendation-card"
import { InlineLoading } from "@/components/loading-spinner"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  recommendations?: DiscoverMusicResponse | null
  timestamp: Date
}

interface AIChatInterfaceProps {
  onRecommendationsReceived?: (recommendations: DiscoverMusicResponse) => void
}

export function AIChatInterface({ onRecommendationsReceived }: AIChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hi! I'm your AI Music Discovery Companion. I can help you find music based on millions of listener reviews and AI analysis. What kind of music are you looking for today?",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const suggestedPrompts = [
    "Songs for a rainy evening",
    "Music like Coldplay but more emotional",
    "Underrated indie rock albums",
    "Music for deep focus",
    "Songs that sound like Interstellar",
    "Relaxing jazz for studying",
    "Energetic workout music",
    "Hidden gems in electronic music"
  ]

  const generateFollowUpQuestions = (userQuery: string) => {
    const questions = [
      "Would you prefer something more upbeat or calmer?",
      "Any specific artists you'd like me to explore?",
      "Should I focus on newer releases or classic tracks?",
      "Do you want music with vocals or instrumental?",
      "Any particular era or decade you prefer?"
    ]
    return questions.slice(0, 3)
  }

  const processUserQuery = async (query: string) => {
    setIsLoading(true)
    setIsTyping(true)

    // Simulate AI thinking
    await new Promise(resolve => setTimeout(resolve, 1500))

    try {
      // Parse the query to extract mood, activity, genres
      const moodKeywords = ["energetic", "relaxed", "happy", "sad", "focused", "romantic", "chill", "excited", "calm", "upbeat"]
      const activityKeywords = ["workout", "coding", "studying", "driving", "partying", "relaxing", "sleeping", "cooking", "focus", "exercise"]
      const genreKeywords = ["rock", "pop", "hip hop", "electronic", "jazz", "classical", "r&b", "country", "indie", "metal"]

      const detectedMood = moodKeywords.find(k => query.toLowerCase().includes(k))
      const detectedActivity = activityKeywords.find(k => query.toLowerCase().includes(k))
      const detectedGenres = genreKeywords.filter(k => query.toLowerCase().includes(k))

      // Call the discover music API
      const result = await apiClient.discoverMusic({
        user_id: "user_1",
        session_id: "session_1",
        mood: detectedMood || undefined,
        activity: detectedActivity || undefined,
        genres: detectedGenres.length > 0 ? detectedGenres : undefined,
        discovery_preference: "balanced",
        limit: 8
      })

      // Generate AI response
      let aiResponse = ""
      if (result.success && result.recommendations.length > 0) {
        aiResponse = `I found ${result.total_count} songs that match your request. Based on the Review AI Discovery Engine analysis of ${result.strategies_used.join(" and ")}, here are personalized recommendations for "${query}":`
        
        if (onRecommendationsReceived) {
          onRecommendationsReceived(result)
        }
      } else {
        aiResponse = `I searched for music matching "${query}" but couldn't find specific recommendations. Let me try a broader search or you could try different keywords.`
      }

      const followUpQuestions = generateFollowUpQuestions(query)

      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: aiResponse,
        recommendations: result.success ? result : null,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])

      // Add follow-up questions after a delay
      if (followUpQuestions.length > 0) {
        setTimeout(() => {
          const followUpMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `To help me find better recommendations, could you tell me: ${followUpQuestions[0]}`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, followUpMessage])
        }, 2000)
      }

    } catch (error) {
      console.error("Chat error:", error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error while processing your request. Please try again.",
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setIsTyping(false)
    }
  }

  const handleSendMessage = () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    processUserQuery(input)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleSuggestedPrompt = (prompt: string) => {
    setInput(prompt)
    inputRef.current?.focus()
  }

  return (
    <div className="flex flex-col h-screen bg-[#0D1117]">
      {/* Header */}
      <div className="border-b border-[#30363d] bg-[#161B22] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[#1DB954] rounded-full flex items-center justify-center">
            <Brain className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-white">AI Music Discovery Companion</h1>
            <p className="text-xs text-gray-400">Powered by Review AI Discovery Engine</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-3xl ${
                message.role === "user"
                  ? "bg-[#1DB954] text-white"
                  : "bg-[#161B22] text-gray-300 border border-[#30363d]"
              } rounded-2xl px-6 py-4`}
            >
              {message.role === "assistant" && (
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="h-4 w-4 text-[#1DB954]" />
                  <span className="text-xs font-medium text-[#1DB954]">AI Assistant</span>
                </div>
              )}
              <p className="text-sm leading-relaxed">{message.content}</p>
              
              {/* Show recommendations inline */}
              {message.recommendations && message.recommendations.success && (
                <div className="mt-4 space-y-4">
                  <div className="flex items-center gap-2 text-xs text-[#1DB954]">
                    <Sparkles className="h-4 w-4" />
                    <span>Found {message.recommendations.total_count} songs via {message.recommendations.strategies_used.join(" + ")}</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {message.recommendations.recommendations.slice(0, 4).map((rec, index) => (
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
              
              <p className="text-xs mt-2 opacity-60">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-[#161B22] border border-[#30363d] rounded-2xl px-6 py-4">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-[#1DB954]" />
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-[#1DB954] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-[#1DB954] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-[#1DB954] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      {messages.length <= 1 && (
        <div className="px-6 py-4 border-t border-[#30363d] bg-[#161B22]/50">
          <p className="text-xs text-gray-400 mb-3">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSuggestedPrompt(prompt)}
                className="px-3 py-1.5 bg-[#21262d] text-gray-300 rounded-full text-xs hover:bg-[#30363d] hover:text-white transition-all border border-[#30363d] flex items-center gap-1"
              >
                <Sparkles className="h-3 w-3" />
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-[#30363d] bg-[#161B22] px-6 py-4">
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about music discovery..."
            className="flex-1 px-4 py-3 bg-[#0D1117] border border-[#30363d] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#1DB954] focus:ring-1 focus:ring-[#1DB954] transition-all"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="px-6 py-3 bg-[#1DB954] text-white rounded-xl font-medium hover:bg-[#1ed760] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {isLoading ? (
              <InlineLoading text="" />
            ) : (
              <>
                <Send className="h-5 w-5" />
                Send
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
