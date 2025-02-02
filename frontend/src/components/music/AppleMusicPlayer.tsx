import * as React from "react";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { toast } from "sonner";
import { music } from "../../lib/api";

export function AppleMusicPlayer() {
  const [isConnected, setIsConnected] = React.useState(false);
  const [currentTrack, setCurrentTrack] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const response = await music.apple.getNowPlaying();
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

  // Track playback handled by Apple Music SDK

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Apple Music Player</CardTitle>
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
          <CardTitle>Apple Music Player</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center space-y-4">
            <p className="text-muted-foreground">
              Connect your Apple Music account to play music during your streams
            </p>
            <Button onClick={() => toast("Apple Music integration coming soon")}>
              Connect Apple Music
            </Button>
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
              {currentTrack.attributes.artwork && (
                <img
                  src={currentTrack.attributes.artwork.url}
                  alt={currentTrack.attributes.name}
                  className="h-16 w-16 rounded-md"
                />
              )}
              <div>
                <h3 className="font-medium">{currentTrack.attributes.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {currentTrack.attributes.artistName}
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
