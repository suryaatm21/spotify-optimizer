/**
 * OAuth callback page for handling Spotify authentication response.
 */
import { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import LoadingSpinner from '@/components/LoadingSpinner';
import Layout from '@/components/Layout';

export default function CallbackPage() {
  const { isLoading } = useAuth();

  return (
    <Layout
      title="Authenticating..."
      description="Processing your Spotify authentication">
      <div className="min-h-screen bg-spotify-gray-900 flex flex-col items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <h1 className="text-2xl font-bold text-white mt-6 mb-2">
            Connecting to Spotify
          </h1>
          <p className="text-spotify-gray-400">
            Please wait while we authenticate your account...
          </p>
        </div>
      </div>
    </Layout>
  );
}
