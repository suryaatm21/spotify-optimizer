# Spotify Playlist Optimizer

A full-stack application that analyzes and optimizes Spotify playlists using machine learning clustering algorithms.

## Features

- **Spotify Integration**: Connect with your Spotify account to analyze your playlists
- **Machine Learning Analysis**: Use K-means and DBSCAN clustering to identify song patterns
- **Visual Analytics**: Interactive charts and tables to explore your music data
- **Optimization Suggestions**: Get AI-powered recommendations to improve your playlists
- **Real-time Updates**: Live data synchronization with your Spotify library

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework for building APIs
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM) library
- **PostgreSQL/SQLite**: Database for storing user and playlist data
- **Scikit-learn**: Machine learning library for clustering algorithms
- **Pandas & NumPy**: Data manipulation and numerical computing
- **Pydantic**: Data validation using Python type annotations

### Frontend
- **Next.js**: React framework with TypeScript
- **Tailwind CSS**: Utility-first CSS framework
- **SWR**: Data fetching library for React
- **Recharts**: Composable charting library for React
- **Lucide React**: Beautiful icons library
- **Axios**: HTTP client for API requests

## Project Structure

```
spotify-optimizer/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── models.py              # SQLAlchemy database models
│   ├── schemas.py             # Pydantic data schemas
│   ├── dependencies.py        # Database and auth dependencies
│   ├── routers/
│   │   ├── auth.py           # Authentication endpoints
│   │   └── analytics.py      # Playlist analysis endpoints
│   ├── services/
│   │   └── clustering.py     # Machine learning clustering service
│   ├── tests/
│   │   ├── conftest.py       # Pytest configuration and fixtures
│   │   └── test_clustering.py # Clustering service tests
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Environment variables template
├── frontend/
│   ├── pages/
│   │   ├── index.tsx         # Dashboard page
│   │   ├── callback.tsx      # OAuth callback page
│   │   ├── _app.tsx          # App configuration
│   │   └── playback-stats/
│   │       └── [playlistId].tsx # Dynamic playlist analysis page
│   ├── components/
│   │   ├── Layout.tsx        # Common page layout
│   │   ├── StatsTable.tsx    # Reusable data table
│   │   ├── ClusterChart.tsx  # PCA scatter plot visualization
│   │   ├── PlaylistCard.tsx  # Playlist display component
│   │   ├── OptimizationPanel.tsx # Suggestions panel
│   │   ├── LoadingSpinner.tsx # Loading indicator
│   │   └── ErrorMessage.tsx  # Error display component
│   ├── lib/
│   │   └── api.ts           # API client and utilities
│   ├── hooks/
│   │   └── useAuth.tsx      # Authentication hook
│   ├── types/
│   │   └── playlist.ts      # TypeScript interfaces
│   ├── styles/
│   │   └── globals.css      # Global styles and Tailwind
│   ├── package.json         # Node.js dependencies
│   ├── next.config.js       # Next.js configuration
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   └── tsconfig.json        # TypeScript configuration
└── README.md               # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- Spotify Developer Account
- PostgreSQL (optional, SQLite included for development)

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Spotify API credentials
   ```

5. **Run the development server:**
   ```bash
   python main.py
   ```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

### Spotify API Setup

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Add `http://localhost:3000/callback` to the Redirect URIs
4. Copy your Client ID and Client Secret to the backend `.env` file

## API Endpoints

### Authentication
- `GET /api/auth/login` - Initiate Spotify OAuth flow
- `POST /api/auth/callback` - Handle OAuth callback
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh access token

### Analytics
- `GET /api/analytics/playlists` - Get user playlists
- `GET /api/analytics/playlists/{id}/tracks` - Get playlist tracks
- `GET /api/analytics/playlists/{id}/stats` - Get playlist statistics
- `POST /api/analytics/playlists/{id}/analyze` - Analyze playlist with clustering
- `GET /api/analytics/playlists/{id}/optimize` - Get optimization suggestions

## Features

### Machine Learning Analysis
- **K-means Clustering**: Groups similar tracks based on audio features
- **DBSCAN Clustering**: Identifies clusters of varying densities
- **PCA Visualization**: 2D projection of high-dimensional audio features
- **Silhouette Analysis**: Measures clustering quality

### Audio Features Analyzed
- Danceability
- Energy
- Speechiness
- Acousticness
- Instrumentalness
- Liveness
- Valence (mood)
- Tempo

### Optimization Suggestions
- Outlier detection and removal recommendations
- Theme consistency analysis
- Energy flow optimization
- Mood diversity suggestions
- Track ordering improvements

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Deployment

### Backend (Railway/Heroku)
1. Set up environment variables in your hosting platform
2. Deploy the FastAPI application
3. Run database migrations

### Frontend (Vercel/Netlify)
1. Connect your GitHub repository
2. Set build command: `npm run build`
3. Set environment variables for API URL

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Spotify Web API for music data
- Scikit-learn for machine learning algorithms
- Next.js and FastAPI communities for excellent documentation
- Tailwind CSS for the design system
