/**
 * PCA scatter plot component for visualizing playlist clusters using Recharts.
 */
import { useMemo } from "react";
import { 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend 
} from "recharts";
import { IClusterData, ITrack } from "@/types/playlist";

interface IClusterChartProps {
  clusters: IClusterData[];
  tracks: ITrack[];
}

interface ScatterDataPoint {
  x: number;
  y: number;
  name: string;
  artist: string;
  cluster: number;
  trackId: number;
}

export default function ClusterChart({ clusters, tracks }: IClusterChartProps) {
  // Generate mock PCA coordinates for visualization
  // In a real implementation, these would come from the backend
  const scatterData = useMemo(() => {
    const data: ScatterDataPoint[] = [];
    const trackMap = new Map(tracks.map(track => [track.id, track]));
    
    clusters.forEach((cluster, clusterIndex) => {
      cluster.track_ids.forEach((trackId, trackIndex) => {
        const track = trackMap.get(trackId);
        if (!track) return;
        
        // Generate mock PCA coordinates based on audio features
        const features = [
          track.danceability || 0.5,
          track.energy || 0.5,
          track.valence || 0.5,
          track.acousticness || 0.5
        ];
        
        // Simple PCA simulation using weighted features
        const x = features[0] * 0.5 + features[1] * 0.3 + Math.random() * 0.3 - 0.15;
        const y = features[2] * 0.5 + features[3] * 0.3 + Math.random() * 0.3 - 0.15;
        
        data.push({
          x: x * 10, // Scale for better visualization
          y: y * 10,
          name: track.name,
          artist: track.artist,
          cluster: cluster.cluster_id,
          trackId: track.id
        });
      });
    });
    
    return data;
  }, [clusters, tracks]);

  // Group data by cluster for different colors
  const clusterGroups = useMemo(() => {
    const groups: { [key: number]: ScatterDataPoint[] } = {};
    
    scatterData.forEach(point => {
      if (!groups[point.cluster]) {
        groups[point.cluster] = [];
      }
      groups[point.cluster].push(point);
    });
    
    return groups;
  }, [scatterData]);

  const clusterColors = [
    "#ef4444", // red-500
    "#3b82f6", // blue-500  
    "#10b981", // emerald-500
    "#f59e0b", // amber-500
    "#8b5cf6", // violet-500
    "#ec4899", // pink-500
    "#6366f1", // indigo-500
    "#f97316"  // orange-500
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-spotify-gray-800 border border-spotify-gray-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-medium">{data.name}</p>
          <p className="text-spotify-gray-300 text-sm">{data.artist}</p>
          <p className="text-spotify-gray-400 text-xs">
            Cluster {data.cluster + 1}
          </p>
          <p className="text-spotify-gray-400 text-xs">
            Position: ({data.x.toFixed(2)}, {data.y.toFixed(2)})
          </p>
        </div>
      );
    }
    return null;
  };

  if (clusters.length === 0 || tracks.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center text-spotify-gray-400">
        <div className="text-center">
          <p className="text-lg mb-2">No cluster data available</p>
          <p className="text-sm">Analyze the playlist to see clusters</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-96 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart
          data={scatterData}
          margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        >
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#404040"
          />
          <XAxis
            type="number"
            dataKey="x"
            domain={["dataMin - 1", "dataMax + 1"]}
            tick={{ fill: "#9ca3af", fontSize: 12 }}
            axisLine={{ stroke: "#6b7280" }}
            tickLine={{ stroke: "#6b7280" }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={["dataMin - 1", "dataMax + 1"]}
            tick={{ fill: "#9ca3af", fontSize: 12 }}
            axisLine={{ stroke: "#6b7280" }}
            tickLine={{ stroke: "#6b7280" }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ color: "#9ca3af" }}
            formatter={(value: string) => (
              <span style={{ color: "#9ca3af" }}>Cluster {parseInt(value) + 1}</span>
            )}
          />
          
          {Object.entries(clusterGroups).map(([clusterId, points]) => (
            <Scatter
              key={clusterId}
              name={clusterId}
              data={points}
              fill={clusterColors[parseInt(clusterId) % clusterColors.length]}
              strokeWidth={2}
              stroke="#1f2937"
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
      
      {/* Cluster Legend */}
      <div className="mt-4 flex flex-wrap gap-3">
        {clusters.map((cluster) => (
          <div
            key={cluster.cluster_id}
            className="flex items-center space-x-2 px-3 py-1 bg-spotify-gray-700 rounded-lg"
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ 
                backgroundColor: clusterColors[cluster.cluster_id % clusterColors.length] 
              }}
            />
            <span className="text-spotify-gray-300 text-sm">
              Cluster {cluster.cluster_id + 1} ({cluster.track_count} tracks)
            </span>
          </div>
        ))}
      </div>
      
      {/* Chart Description */}
      <div className="mt-4 text-center">
        <p className="text-spotify-gray-400 text-sm">
          PCA visualization of track audio features. Each point represents a track, 
          colored by cluster assignment.
        </p>
      </div>
    </div>
  );
}
