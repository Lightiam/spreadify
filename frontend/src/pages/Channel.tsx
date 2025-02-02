import * as React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Channel as ChannelType, Stream } from "../types";
import { channels, streams } from "../lib/api";
import { formatDate, formatViewCount } from "../lib/utils";
import { Button } from "../components/ui/button";

import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { ScheduleStreamDialog } from "../components/streams/ScheduleStreamDialog";
import { SubscribeButton } from "../components/channels/SubscribeButton";
import { DonateDialog } from "../components/channels/DonateDialog";
import { ChannelAnalytics } from "../components/channels/ChannelAnalytics";

export default function Channel() {
  const { id } = useParams<{ id: string }>();
  const [channel, setChannel] = React.useState<ChannelType | null>(null);
  const [channelStreams, setChannelStreams] = React.useState<Stream[]>([]);
  const [newStream, setNewStream] = React.useState({ title: "", description: "" });
  const [isCreating, setIsCreating] = React.useState(false);
  const [showScheduleDialog, setShowScheduleDialog] = React.useState(false);
  const [showDonateDialog, setShowDonateDialog] = React.useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    if (!id) return;
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const channelResponse = await channels.get(id!);
      setChannel(channelResponse.data);

      const streamsResponse = await streams.list(id!);
      setChannelStreams(streamsResponse.data);
    } catch (error) {
      console.error('Error fetching channel data:', error);
      toast({
        title: "Error",
        description: "Failed to load channel data",
        variant: "destructive"
      });
    }
  };

  const handleCreateStream = async () => {
    if (!id || !newStream.title.trim()) return;
    setIsCreating(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/channels/${id}/streams`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newStream),
      });
      
      if (!response.ok) throw new Error('Failed to create stream');
      
      toast({
        description: "Stream created successfully"
      });
      setNewStream({ title: "", description: "" });
      fetchData();
    } catch (error) {
      toast({
        description: "Failed to create stream",
        variant: "destructive"
      });
    } finally {
      setIsCreating(false);
    }
  };

  if (!channel) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold">{channel.name}</h1>
            <p className="text-muted-foreground">
              {channel.subscriberCount} subscribers
            </p>
          </div>
          <div className="flex gap-2">
            <SubscribeButton channelId={id!} onSubscriptionChange={fetchData} />
            <Button variant="outline" onClick={() => setShowDonateDialog(true)}>
              Donate
            </Button>
          </div>
        </div>
          <Dialog>
            <div className="flex gap-2">
              <DialogTrigger asChild>
                <Button>Create Stream</Button>
              </DialogTrigger>
              <Button variant="outline" onClick={() => setShowScheduleDialog(true)}>
                Schedule Stream
              </Button>
            </div>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Stream</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Input
                    placeholder="Stream Title"
                    value={newStream.title}
                    onChange={(e) =>
                      setNewStream({ ...newStream, title: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Textarea
                    placeholder="Stream Description"
                    value={newStream.description}
                    onChange={(e) =>
                      setNewStream({ ...newStream, description: e.target.value })
                    }
                  />
                </div>
                <Button
                  className="w-full"
                  onClick={handleCreateStream}
                  disabled={isCreating}
                >
                  {isCreating ? "Creating..." : "Create Stream"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        )}

        <ScheduleStreamDialog
          channelId={id!}
          open={showScheduleDialog}
          onOpenChange={setShowScheduleDialog}
          onScheduled={fetchData}
        />

        <DonateDialog
          channelId={id!}
          open={showDonateDialog}
          onOpenChange={setShowDonateDialog}
        />
      </div>

      <ScheduleStreamDialog
        channelId={id!}
        open={showScheduleDialog}
        onOpenChange={setShowScheduleDialog}
        onScheduled={fetchData}
      />

      <DonateDialog
        channelId={id!}
        open={showDonateDialog}
        onOpenChange={setShowDonateDialog}
      />

      <div className="mt-8">
        <ChannelAnalytics channelId={id!} />
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Channel Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold">Description</h3>
                <p className="text-muted-foreground">
                  {channel.description || "No description"}
                </p>
              </div>
              <div>
                <h3 className="font-semibold">Created</h3>
                <p className="text-muted-foreground">
                  {formatDate(channel.createdAt)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Streams</CardTitle>
          </CardHeader>
          <CardContent>
            {channelStreams.length === 0 ? (
              <p className="text-muted-foreground">No streams yet</p>
            ) : (
              <div className="space-y-4">
                {channelStreams.map((stream) => (
                  <div
                    key={stream.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div>
                      <h3 className="font-semibold">{stream.title}</h3>
                      <p className="text-sm text-muted-foreground">
                        {stream.status === 'live'
                          ? `${formatViewCount(stream.viewerCount)} viewers`
                          : formatDate(stream.createdAt)}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/streams/${stream.id}`)}
                    >
                      {stream.status === 'live' ? 'View' : 'Manage'}
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
