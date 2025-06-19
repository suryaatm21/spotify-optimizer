/**
 * Error message component with retry functionality.
 */
import { AlertCircle, RefreshCw } from "lucide-react";

interface IErrorMessageProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

export default function ErrorMessage({ 
  message, 
  onRetry, 
  className = "" 
}: IErrorMessageProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
      <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
      <h3 className="text-lg font-semibold text-white mb-2">Error</h3>
      <p className="text-spotify-gray-300 text-center mb-4 max-w-md">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center space-x-2 px-4 py-2 bg-spotify-green hover:bg-spotify-green/90 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Try Again</span>
        </button>
      )}
    </div>
  );
}
