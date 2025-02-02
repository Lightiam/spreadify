import * as React from "react";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { toast } from "sonner";
import { music } from "../../lib/api";

export function SpotifyPlayer() {
  const [isConnected, setIsConnected] = React.useState(false);
  const [currentTrack, setCurrentTrack] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const response = await music.spotify.getNowPlaying();
      setIsConnected(true);
      setCurrentTrack(response.data);
    } catch (error: any) {
      if (error.response?.status === 400) {
        setIsConnected(false);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const response = await music.spotify.getAuthUrl();
      window.location.href = response.data.url;
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to Spotify",
        variant: "destructive",
      });
    }
  };

  // Track playback handled by Spotify SDK

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Spotify Player</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-4">
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!isConnected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Spotify Player</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center space-y-4">
            <p className="text-muted-foreground">
              Connect your Spotify account to play music during your streams
            </p>
            <Button onClick={handleConnect}>Connect Spotify</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Now Playing</CardTitle>
      </CardHeader>
      <CardContent>
        {currentTrack ? (
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              {currentTrack.item.album.images[0] && (
                <img
                  src={currentTrack.item.album.images[0].url}
                  alt={currentTrack.item.name}
                  className="h-16 w-16 rounded-md"
                />
              )}
              <div>
                <h3 className="font-medium">{currentTrack.item.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {currentTrack.item.artists.map((a: any) => a.name).join(", ")}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-center text-muted-foreground">No track playing</p>
        )}
      </CardContent>
    </Card>
  );
}
