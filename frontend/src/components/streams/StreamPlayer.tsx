import * as React from "react";
import Hls from "hls.js";

interface StreamPlayerProps {
  streamKey: string | undefined;
  autoPlay?: boolean;
  muted?: boolean;
  controls?: boolean;
  onQualityChange?: (quality: string) => void;
}

interface Quality {
  height: number;
  width: number;
  bitrate: number;
  name: string;
}

export function StreamPlayer({
  streamKey,
  autoPlay = true,
  muted = false,
  controls = true,
  onQualityChange,
}: StreamPlayerProps) {
  const [currentQuality, setCurrentQuality] = React.useState<string>("auto");
  const [availableQualities, setAvailableQualities] = React.useState<Quality[]>([]);
  const [isQualityMenuOpen, setIsQualityMenuOpen] = React.useState(false);
  const [overlays, setOverlays] = React.useState<Array<{
    id: string;
    path: string;
    position_x: number;
    position_y: number;
    scale: number;
  }>>([]);
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const hlsRef = React.useRef<Hls | null>(null);

  // Fetch overlays when stream key changes
  React.useEffect(() => {
    if (!streamKey) return;
    
    const fetchOverlays = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/overlays/${streamKey}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch overlays: ${response.statusText}`);
        }
        const data = await response.json();
        if (!Array.isArray(data)) {
          throw new Error("Invalid overlay data format");
        }
        setOverlays(data);
      } catch (error) {
        console.error("Failed to fetch overlays:", error);
        setOverlays([]);
      }
    };
    
    fetchOverlays();
    // Refresh overlays every 30 seconds
    const intervalId = setInterval(fetchOverlays, 30000);
    return () => clearInterval(intervalId);
  }, [streamKey]);

  React.useEffect(() => {
    if (!videoRef.current) return;

    const loadStream = async () => {
      const video = videoRef.current!;
      const streamUrl = `${import.meta.env.VITE_HLS_SERVER_URL}/${streamKey}/master.m3u8`;

      if (!streamKey) return;
      
      if (Hls.isSupported()) {
        if (hlsRef.current) {
          hlsRef.current.destroy();
        }

        const hls = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
          backBufferLength: 90,
          maxBufferLength: 30,
          maxMaxBufferLength: 600,
          maxBufferSize: 60 * 1000 * 1000,
          maxBufferHole: 0.5,
          liveSyncDurationCount: 3,
          liveMaxLatencyDurationCount: 10,
          liveDurationInfinity: true,
          startLevel: -1,
          capLevelToPlayerSize: true,
          debug: true
        });

        hlsRef.current = hls;
        hls.loadSource(streamUrl);
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, (_, data) => {
          const qualities = data.levels.map((level: any) => ({
            height: level.height,
            width: level.width,
            bitrate: level.bitrate,
            name: `${level.height}p`
          }));
          
          setAvailableQualities(qualities);
          if (autoPlay) {
            video.play().catch(console.error);
          }
        });
        
        hls.on(Hls.Events.LEVEL_SWITCHED, (_, data) => {
          const quality = availableQualities[data.level];
          if (quality) {
            setCurrentQuality(quality.name);
            onQualityChange?.(quality.name);
          }
        });

        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal) {
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                hls.startLoad();
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                hls.recoverMediaError();
                break;
              default:
                hls.destroy();
                break;
            }
          }
        });
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = streamUrl;
        video.addEventListener("loadedmetadata", () => {
          if (autoPlay) {
            video.play().catch(console.error);
          }
        });
      }
    };

    loadStream();

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [streamKey, autoPlay]);

  return (
    <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
      <div className="relative">
        <video
          ref={videoRef}
          className="w-full h-full"
          playsInline
          muted={muted}
          controls={controls}
        />
        <div className="absolute inset-0 pointer-events-none">
          {overlays.map((overlay) => (
            <img
              key={overlay.id}
              src={overlay.path}
              alt=""
              className="absolute"
              style={{
                left: `${overlay.position_x}px`,
                top: `${overlay.position_y}px`,
                transform: `scale(${overlay.scale})`,
                transformOrigin: "top left",
                zIndex: 10
              }}
            />
          ))}
        </div>
        {availableQualities.length > 0 && (
          <div className="absolute bottom-16 right-4">
            <button
              className="flex items-center gap-1 bg-black/80 hover:bg-black/90 text-white text-sm px-3 py-1.5 rounded-lg"
              onClick={() => setIsQualityMenuOpen(!isQualityMenuOpen)}
            >
              <span>{currentQuality}</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m6 9 6 6 6-6"/>
              </svg>
            </button>
            
            {isQualityMenuOpen && (
              <div className="absolute bottom-full right-0 mb-1 bg-black/80 rounded-lg overflow-hidden">
                <div className="py-1">
                  <button
                    className={`w-full px-4 py-1.5 text-sm text-left hover:bg-white/10 ${currentQuality === "auto" ? "text-blue-400" : "text-white"}`}
                    onClick={() => {
                      if (hlsRef.current) {
                        hlsRef.current.currentLevel = -1;
                        setCurrentQuality("auto");
                      }
                      setIsQualityMenuOpen(false);
                    }}
                  >
                    Auto
                  </button>
                  {availableQualities.map((quality) => (
                    <button
                      key={quality.name}
                      className={`w-full px-4 py-1.5 text-sm text-left hover:bg-white/10 ${currentQuality === quality.name ? "text-blue-400" : "text-white"}`}
                      onClick={() => {
                        const level = availableQualities.findIndex(q => q.name === quality.name);
                        if (hlsRef.current && level !== -1) {
                          hlsRef.current.currentLevel = level;
                          setCurrentQuality(quality.name);
                        }
                        setIsQualityMenuOpen(false);
                      }}
                    >
                      {quality.name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
