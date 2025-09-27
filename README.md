# Spotify Playlist Optimizer

A comprehensive machine learning application that analyzes and manages Spotify playlists using advanced clustering algorithms and audio feature analysis.

## Watch the Demo (Click Thumbnail)

[![Watch the demo](https://i.imgur.com/gQuY5X9.png)](https://youtu.be/oDh19udD8h0)


## ✨ Key Features

### 🎵 Playlist Analysis

- **Multi-Algorithm Clustering**: K-Means, DBSCAN
- **Audio Feature Analysis**: Integration with ReccoBeats API for enhanced audio features
- **Interactive Visualization**: PCA scatter plots with cluster coloring and tooltips
- **Quality Metrics**: Silhouette scores and cluster quality assessment

### 🛠️ Playlist Management (CRUD Operations)

- **Create**: New playlist creation with customizable settings
- **Read**: Detailed playlist metadata and track information
- **Update**: Modify playlist name, description, and privacy settings
- **Delete**: Safe playlist removal with confirmation dialogs
- **Track Management**: Add/remove tracks with Spotify search integration

### 📊 Smart Analytics

- **Behavioral Modeling**: Skip pattern analysis and engagement scoring
- **Hidden Gem Detection**: Identification of underappreciated tracks
- **Performance Metrics**: Track and playlist performance insights
- **Optimization Suggestions**: Data-driven recommendations (coming soon)

### 🎨 Modern UI/UX

- **Spotify-Themed Design**: Consistent branding with dark theme
- **Responsive Layout**: Mobile-friendly adaptive components
- **Real-time Updates**: Live clustering and analysis controls
- **Interactive Components**: Drag-and-drop and search functionality

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Spotify Developer Account
- PostgreSQL (optional, SQLite included)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configure Spotify API credentials in .env
python main.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Database Initialization

```bash
cd scripts
python init_database.py
```

## 🏗️ Technical Architecture

### Backend Stack

- **FastAPI**: REST API with automatic OpenAPI documentation
- **SQLAlchemy**: Database ORM with PostgreSQL/SQLite support
- **Async Processing**: Non-blocking audio feature fetching
- **Pydantic**: Type-safe data validation and serialization

### Frontend Stack

- **Next.js 14**: React framework with App Router
- **TypeScript**: Strict type checking for reliability
- **Tailwind CSS**: Utility-first styling system
- **SWR**: Data fetching and caching library
- **Recharts**: Interactive data visualization

### External Integrations

- **Spotify Web API**: Playlist and track data access
- **ReccoBeats API**: Enhanced audio feature analysis
- **OAuth 2.0**: Secure authentication flow

## 📱 Usage Guide

### 1. Authentication

- Log in with your Spotify account
- Grant necessary permissions for playlist access

### 2. Playlist Analysis

- Import playlists from your Spotify library
- Choose clustering algorithm (K-Means or DBSCAN)
- Analyze audio features and view cluster visualizations

### 3. Playlist Management

- **Create**: Click "New Playlist" to create fresh playlists
- **Edit**: Use the Playlist tab to modify metadata
- **Tracks**: Add/remove tracks via search or bulk operations
- **Organize**: Use clustering insights to optimize track order

### 4. Insights & Optimization

- View detailed statistics and audio feature analysis
- Identify patterns in your music preferences
- Get recommendations for playlist improvements

## 🛠️ API Endpoints

### Authentication

- `GET /auth/login` - Initiate Spotify OAuth flow
- `GET /auth/callback` - Handle OAuth callback
- `POST /auth/logout` - Logout user

### Playlist CRUD

- `POST /api/playlists` - Create new playlist
- `GET /api/playlists/{id}` - Get playlist metadata
- `PUT /api/playlists/{id}` - Update playlist
- `DELETE /api/playlists/{id}` - Delete playlist

### Track Management

- `POST /api/playlists/{id}/tracks` - Add tracks to playlist
- `DELETE /api/playlists/{id}/tracks/{trackId}` - Remove track
- `GET /api/search` - Search Spotify catalog

### Analytics

- `POST /api/analytics/playlists/{id}/analyze` - Run clustering analysis
- `GET /api/analytics/playlists/{id}/stats` - Get playlist statistics
- `GET /api/analytics/playlists/{id}/tracks` - Get detailed track data

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
python -m pytest tests/
```

### Run Frontend Tests

```bash
cd frontend
npm test
```

## 🚧 Development Status

### ✅ Completed Features

- [x] Multi-algorithm clustering engine
- [x] Interactive PCA visualization
- [x] Spotify OAuth authentication
- [x] Playlist CRUD operations
- [x] Track management with search
- [x] Audio feature analysis
- [x] Responsive UI design
- [x] Real-time sync with Spotify API
- [x] Bulk track operations with success feedback
- [x] Enhanced error handling and user feedback
- [x] Scrollable tables with resizable columns

### 🔄 In Progress

- [ ] Advanced optimization algorithms - Gaussian Mixture, Spectral clustering
- [ ] Playlist collaboration features

### 📋 Planned Features

- [ ] Advanced recommendation engine
- [ ] Historical analysis tracking
- [ ] Measuring skip rate to identify overplayed/underplayed songs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Spotify** for their comprehensive Web API
- **ReccoBeats** for enhanced audio feature analysis
- **scikit-learn** for machine learning algorithms
- **Next.js** and **FastAPI** for excellent frameworks

---

**Status**: Production-ready with active development  
**Last Updated**: August 12, 2025  
**Version**: 4.0.0 - CRUD Features Complete ✨

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
│   ├── create_db.py           # Database initialization script
│   ├── routers/
│   │   ├── auth.py           # Authentication endpoints
│   │   └── analytics.py      # Playlist analysis endpoints
│   ├── services/
│   │   ├── clustering.py     # Machine learning clustering service
│   │   └── audio_features.py # Audio features data quality service
│   ├── tests/
│   │   ├── conftest.py       # Pytest configuration and fixtures
│   │   ├── test_clustering.py # Clustering service tests
│   │   └── test_audio_features.py # Audio features service tests
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Environment variables template
├── db/
│   ├── spotify.db            # Main application database
│   ├── check_db.py           # Database inspection utility
│   ├── monitor_oauth.py      # OAuth flow monitoring utility
│   └── debug_oauth_flow.py   # OAuth debugging utility
├── tests/
│   ├── test_auth_flow.py     # Integration tests for authentication
│   └── direct_oauth_test.py  # Direct OAuth testing utility
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
├── docs/
│   └── refactor-summary.md  # Documentation of project refactor
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

5. **Initialize the database:**

   ```bash
   python create_db.py
   ```

6. **Navigate back to the root directory and run the development server:**

   ```bash
   cd ..
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Alternatively, you can run from the backend directory:

   ```bash
   cd backend
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
- `GET /api/analytics/playlists/{id}/data-quality` - Check audio features data quality
- `POST /api/analytics/playlists/{id}/analyze` - Analyze playlist with clustering (includes data quality improvements)
- `GET /api/analytics/playlists/{id}/optimize` - Get optimization suggestions

## Features

### Machine Learning Analysis

- **K-means Clustering**: Groups similar tracks based on audio features
- **DBSCAN Clustering**: Identifies clusters of varying densities
- **PCA Visualization**: 2D projection of high-dimensional audio features
- **Silhouette Analysis**: Measures clustering quality
- **Data Quality Management**: Intelligent handling of missing audio features
  - Automatic fetching of missing features from Spotify API
  - KNN-based imputation for remaining missing values
  - Statistical fallbacks and quality reporting
- **Improved Analysis Accuracy**: Enhanced clustering reliability through better data preparation

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
