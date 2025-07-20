/**
 * Reusable loading spinner component with different sizes.
 */
import { Loader2 } from 'lucide-react';

interface ILoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

export default function LoadingSpinner({
  size = 'medium',
  className = '',
}: ILoadingSpinnerProps) {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12',
  };

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <Loader2
        className={`animate-spin text-spotify-green ${sizeClasses[size]}`}
      />
    </div>
  );
}
