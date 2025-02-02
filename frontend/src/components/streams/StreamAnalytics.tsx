import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { analytics } from "../../lib/api";
import { toast } from "sonner";

interface StreamAnalyticsProps {
  streamId: string;
}

interface AnalyticsResponse {
  data: {
    viewerCount: number[];
    chatMessages: number[];
    superChats: number[];
    timestamps: string[];
  };
}

interface StreamStats {
  viewerCount: number[];
  chatMessages: number[];
  superChats: number[];
  timestamps: string[];
}

export function StreamAnalytics({ streamId }: StreamAnalyticsProps) {
  const [stats, setStats] = React.useState<StreamStats | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await analytics.getStreamStats(streamId) as AnalyticsResponse;
        setStats(response.data);
      } catch (error) {
        toast("Failed to load analytics data");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, [streamId]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Stream Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-6">
            <p className="text-muted-foreground">Loading analytics...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Stream Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-6">
            <p className="text-muted-foreground">No analytics data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = stats.timestamps.map((timestamp, index) => ({
    timestamp,
    viewers: stats.viewerCount[index],
    messages: stats.chatMessages[index],
    superChats: stats.superChats[index],
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Stream Analytics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 text-sm font-medium">Viewer Count</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) =>
                    new Date(value).toLocaleString()
                  }
                />
                <Line
                  type="monotone"
                  dataKey="viewers"
                  stroke="#2563eb"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-medium">Chat Activity</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) =>
                    new Date(value).toLocaleString()
                  }
                />
                <Line
                  type="monotone"
                  dataKey="messages"
                  stroke="#16a34a"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="superChats"
                  stroke="#eab308"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Peak Viewers</p>
              <p className="text-2xl font-bold">
                {Math.max(...stats.viewerCount)}
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Total Messages</p>
              <p className="text-2xl font-bold">
                {stats.chatMessages[stats.chatMessages.length - 1]}
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Super Chats</p>
              <p className="text-2xl font-bold">
                {stats.superChats[stats.superChats.length - 1]}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
