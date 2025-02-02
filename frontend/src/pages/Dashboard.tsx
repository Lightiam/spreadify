import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { toast } from "sonner";
import { Channel, Stream } from "../types";
import { formatDate, formatViewCount } from "../lib/utils";

export default function Dashboard() {
  const [channels, setChannels] = React.useState<Channel[]>([]);
  const [liveStreams, setLiveStreams] = React.useState<Stream[]>([]);
  const [newChannel, setNewChannel] = React.useState({ name: "", description: "" });
  const [isCreating, setIsCreating] = React.useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/channels`);
      const channelsData = await response.json();
      setChannels(channelsData);

      const activeStreams: Stream[] = [];
      for (const channel of channelsData) {
        const streamsResponse = await fetch(`${import.meta.env.VITE_API_URL}/channels/${channel.id}/streams`);
        const streamsData = await streamsResponse.json();
        const liveStreams = streamsData.filter((s: Stream) => s.status === 'live');
        activeStreams.push(...liveStreams);
      }
      setLiveStreams(activeStreams);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast({
        description: "Failed to load dashboard data",
        variant: "destructive",
      });
    }
  };

  const handleCreateChannel = async () => {
    if (!newChannel.name.trim()) return;
    setIsCreating(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/channels`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newChannel),
      });
      
      if (!response.ok) throw new Error('Failed to create channel');
      
      toast({
        description: "Channel created successfully",
      });
      setNewChannel({ name: "", description: "" });
      fetchData();
    } catch (error) {
      toast({
        description: "Failed to create channel",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Dialog>
          <DialogTrigger asChild>
            <Button>Create Channel</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Channel</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Input
                  placeholder="Channel Name"
                  value={newChannel.name}
                  onChange={(e) =>
                    setNewChannel({ ...newChannel, name: e.target.value })
                  }
                />
              </div>
              <div>
                <Textarea
                  placeholder="Channel Description"
                  value={newChannel.description}
                  onChange={(e) =>
                    setNewChannel({ ...newChannel, description: e.target.value })
                  }
                />
              </div>
              <Button
                className="w-full"
                onClick={handleCreateChannel}
                disabled={isCreating}
              >
                {isCreating ? "Creating..." : "Create Channel"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Your Channels</CardTitle>
          </CardHeader>
          <CardContent>
            {channels.length === 0 ? (
              <p className="text-muted-foreground">No channels yet</p>
            ) : (
              <div className="space-y-4">
                {channels.map((channel) => (
                  <div
                    key={channel.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div>
                      <h3 className="font-semibold">{channel.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        Created {formatDate(channel.createdAt)}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/channels/${channel.id}`)}
                    >
                      Manage
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Live Streams</CardTitle>
          </CardHeader>
          <CardContent>
            {liveStreams.length === 0 ? (
              <p className="text-muted-foreground">No active streams</p>
            ) : (
              <div className="space-y-4">
                {liveStreams.map((stream) => (
                  <div
                    key={stream.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div>
                      <h3 className="font-semibold">{stream.title}</h3>
                      <p className="text-sm text-muted-foreground">
                        {formatViewCount(stream.viewerCount)} viewers
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/streams/${stream.id}`)}
                    >
                      View
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
