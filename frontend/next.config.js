/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // Proxy to FastAPI backend
      },
    ]
  },
  images: {
    domains: ['i.scdn.co'], // Spotify image domains
  },
}

module.exports = nextConfig
