/**
 * Optimization panel component for displaying playlist optimization suggestions.
 */
import { useState } from "react";
import { Lightbulb, TrendingUp, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { IOptimizationSuggestion } from "@/types/playlist";

interface IOptimizationPanelProps {
  suggestions: IOptimizationSuggestion[];
  onRefresh?: () => void;
}

export default function OptimizationPanel({ 
  suggestions, 
  onRefresh 
}: IOptimizationPanelProps) {
  const [expandedSuggestions, setExpandedSuggestions] = useState<Set<number>>(new Set());

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedSuggestions);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSuggestions(newExpanded);
  };

  const getSuggestionTypeIcon = (type: string) => {
    switch (type) {
      case "outlier_removal":
        return "🎯";
      case "theme_consistency":
        return "🎵";
      case "energy_balance":
        return "⚡";
      case "mood_diversity":
        return "🌈";
      case "mood_balance":
        return "😊";
      default:
        return "💡";
    }
  };

  const getSuggestionTypeColor = (type: string) => {
    switch (type) {
      case "outlier_removal":
        return "text-red-400";
      case "theme_consistency":
        return "text-blue-400";
      case "energy_balance":
        return "text-yellow-400";
      case "mood_diversity":
        return "text-purple-400";
      case "mood_balance":
        return "text-green-400";
      default:
        return "text-spotify-gray-300";
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return "text-green-400";
    if (score >= 0.6) return "text-yellow-400";
    return "text-red-400";
  };

  if (suggestions.length === 0) {
    return (
      <div className="bg-spotify-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Lightbulb className="h-5 w-5 text-yellow-400" />
            <span>Optimization Suggestions</span>
          </h2>
          
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 bg-spotify-gray-700 hover:bg-spotify-gray-600 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          )}
        </div>
        
        <div className="text-center py-8">
          <Lightbulb className="h-12 w-12 text-spotify-gray-500 mx-auto mb-3" />
          <p className="text-spotify-gray-400">
            No optimization suggestions available. Analyze the playlist to get recommendations.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-spotify-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-spotify-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Lightbulb className="h-5 w-5 text-yellow-400" />
          <span>Optimization Suggestions</span>
        </h2>
        
        <div className="flex items-center space-x-2">
          <span className="text-spotify-gray-400 text-sm">
            {suggestions.length} suggestions
          </span>
          
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 bg-spotify-gray-700 hover:bg-spotify-gray-600 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {suggestions.map((suggestion, index) => (
          <div
            key={index}
            className="bg-spotify-gray-700/50 rounded-lg p-4 border border-spotify-gray-600"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <div className="text-2xl">
                  {getSuggestionTypeIcon(suggestion.suggestion_type)}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className={`font-medium ${getSuggestionTypeColor(suggestion.suggestion_type)}`}>
                      {suggestion.suggestion_type.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                    </h3>
                    
                    <div className="flex items-center space-x-1">
                      <span className="text-xs text-spotify-gray-500">Confidence:</span>
                      <span className={`text-xs font-medium ${getConfidenceColor(suggestion.confidence_score)}`}>
                        {Math.round(suggestion.confidence_score * 100)}%
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-spotify-gray-300 text-sm leading-relaxed">
                    {suggestion.description}
                  </p>
                  
                  {expandedSuggestions.has(index) && (
                    <div className="mt-3 pt-3 border-t border-spotify-gray-600">
                      <div className="flex items-center space-x-2 mb-2">
                        <TrendingUp className="h-4 w-4 text-spotify-gray-400" />
                        <span className="text-xs text-spotify-gray-400 font-medium">
                          Affected Tracks: {suggestion.affected_tracks.length}
                        </span>
                      </div>
                      
                      <div className="text-xs text-spotify-gray-500">
                        Track IDs: {suggestion.affected_tracks.slice(0, 5).join(", ")}
                        {suggestion.affected_tracks.length > 5 && "..."}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <button
                onClick={() => toggleExpanded(index)}
                className="p-1 hover:bg-spotify-gray-600 rounded transition-colors"
              >
                {expandedSuggestions.has(index) ? (
                  <ChevronUp className="h-4 w-4 text-spotify-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-spotify-gray-400" />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
      
      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-spotify-gray-600">
        <div className="flex items-center justify-between text-sm">
          <span className="text-spotify-gray-400">
            Average confidence score:
          </span>
          <span className={`font-medium ${getConfidenceColor(
            suggestions.reduce((acc, s) => acc + s.confidence_score, 0) / suggestions.length
          )}`}>
            {Math.round(
              (suggestions.reduce((acc, s) => acc + s.confidence_score, 0) / suggestions.length) * 100
            )}%
          </span>
        </div>
      </div>
    </div>
  );
}
