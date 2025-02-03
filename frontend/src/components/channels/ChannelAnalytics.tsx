import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { analytics } from "../../lib/api";
import { toast } from "sonner";

interface ChannelAnalyticsProps {
  channelId: string;
}

interface ChannelStats {
  subscriberGrowth: number[];
  streamCounts: number[];
  viewerCounts: number[];
  superChatRevenue: number[];
  donationRevenue: number[];
  timestamps: string[];
}

export function ChannelAnalytics({ channelId }: ChannelAnalyticsProps) {
  const [stats, setStats] = React.useState<ChannelStats | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await analytics.getChannelStats(channelId);
        setStats(response.data);
      } catch (error) {
        toast("Failed to load channel analytics");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [channelId]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Channel Analytics</CardTitle>
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
          <CardTitle>Channel Analytics</CardTitle>
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
    subscribers: stats.subscriberGrowth[index],
    streams: stats.streamCounts[index],
    viewers: stats.viewerCounts[index],
    superChats: stats.superChatRevenue[index],
    donations: stats.donationRevenue[index],
  }));

  const totalRevenue = stats.superChatRevenue.reduce((a, b) => a + b, 0) +
    stats.donationRevenue.reduce((a, b) => a + b, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Channel Analytics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Total Subscribers</p>
              <p className="text-2xl font-bold">
                {stats.subscriberGrowth[stats.subscriberGrowth.length - 1]}
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Total Streams</p>
              <p className="text-2xl font-bold">
                {stats.streamCounts[stats.streamCounts.length - 1]}
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Total Revenue</p>
              <p className="text-2xl font-bold">${totalRevenue.toFixed(2)}</p>
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-medium">Subscriber Growth</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) =>
                    new Date(value).toLocaleDateString()
                  }
                />
                <Line
                  type="monotone"
                  dataKey="subscribers"
                  stroke="#2563eb"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-medium">Revenue</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) =>
                    new Date(value).toLocaleDateString()
                  }
                />
                <Bar dataKey="superChats" fill="#eab308" stackId="revenue" />
                <Bar dataKey="donations" fill="#16a34a" stackId="revenue" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
