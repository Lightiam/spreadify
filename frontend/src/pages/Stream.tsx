import * as React from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { Socket } from "socket.io-client";
import { Copy, Settings, BarChart } from "lucide-react";

import { Stream as StreamType, ChatMessage } from "../types";
import { streams, chat } from "../lib/api";
import { formatViewCount } from "../lib/utils";
import { hasStreamPermission, canSendSuperChat } from "../lib/security";

import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { SuperChatDialog } from "../components/streams/SuperChatDialog";
import { StreamAnalytics } from "../components/streams/StreamAnalytics";

type OverlayPosition = "top-left" | "top-right" | "bottom-left" | "bottom-right";

interface OverlaySettings {
  title: string;
  logo: string;
  showViewerCount: boolean;
  customText: string;
  position: OverlayPosition;
}

export default function Stream() {
  const { id } = useParams<{ id: string }>();
  const [stream, setStream] = React.useState<StreamType | null>(null);
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = React.useState("");
  const [socket, setSocket] = React.useState<typeof Socket | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [streamKey, setStreamKey] = React.useState<string>("");
  const [showSettings, setShowSettings] = React.useState(false);
  const [showSuperChat, setShowSuperChat] = React.useState(false);
  const [showAnalytics, setShowAnalytics] = React.useState(false);
  const [peerConnection, setPeerConnection] = React.useState<RTCPeerConnection | null>(null);
  const [connectionState, setConnectionState] = React.useState<RTCPeerConnectionState>('new');
  const [retryCount, setRetryCount] = React.useState(0);
  const [isRecovering, setIsRecovering] = React.useState(false);
  const MAX_RETRY_ATTEMPTS = 3;
  const RECOVERY_TIMEOUT = 30000; // 30 seconds
  const BACKOFF_MAX_DELAY = 10000; // 10 seconds

  const cleanupWebRTCResources = React.useCallback(() => {
    const cleanupStartTime = Date.now();
    console.log('Starting WebRTC cleanup...');
    
    if (peerConnection) {
      try {
        const initialState = {
          iceConnectionState: peerConnection.iceConnectionState,
          iceGatheringState: peerConnection.iceGatheringState,
          connectionState: peerConnection.connectionState,
          signalingState: peerConnection.signalingState,
          transceivers: peerConnection.getTransceivers().length,
          senders: peerConnection.getSenders().length,
          receivers: peerConnection.getReceivers().length
        };
        
        console.log('Connection state before cleanup:', initialState);

        // Cleanup transceivers and their tracks
        const transceivers = peerConnection.getTransceivers();
        console.log(`Cleaning up ${transceivers.length} transceivers...`);
        
        let transceiversCleaned = 0;
        transceivers.forEach((transceiver, index) => {
          try {
            const trackType = transceiver.receiver.track?.kind || 'unknown';
            console.log(`Processing transceiver ${index} (${trackType})...`);
            
            if (transceiver.stop) {
              transceiver.stop();
              transceiversCleaned++;
            }
            if (transceiver.receiver.track) {
              transceiver.receiver.track.stop();
            }
            if (transceiver.sender.track) {
              transceiver.sender.track.stop();
            }
          } catch (error) {
            console.error(`Error cleaning up transceiver ${index}:`, error);
          }
        });

        // Cleanup senders and their tracks
        const senders = peerConnection.getSenders();
        console.log(`Cleaning up ${senders.length} senders...`);
        
        let sendersCleaned = 0;
        senders.forEach((sender, index) => {
          try {
            if (sender.track) {
              const trackType = sender.track.kind;
              console.log(`Stopping sender track ${index} (${trackType})...`);
              sender.track.stop();
              sendersCleaned++;
            }
          } catch (error) {
            console.error(`Error cleaning up sender ${index}:`, error);
          }
        });

        // Close peer connection
        console.log('Closing peer connection...');
        peerConnection.close();
        setPeerConnection(null);
        setConnectionState('new');
        
        console.log('Peer connection cleanup completed', {
          transceiversCleaned,
          sendersCleaned,
          durationMs: Date.now() - cleanupStartTime
        });
      } catch (error) {
        console.error('Error during peer connection cleanup:', error);
      }
    }

    // Cleanup video element and media stream
    if (videoRef.current) {
      try {
        const mediaStream = videoRef.current.srcObject as MediaStream;
        if (mediaStream) {
          const tracks = mediaStream.getTracks();
          console.log(`Cleaning up ${tracks.length} media tracks...`);
          
          let tracksCleaned = 0;
          tracks.forEach((track) => {
            try {
              console.log(`Stopping media track (${track.kind}, enabled: ${track.enabled}, muted: ${track.muted})...`);
              track.stop();
              mediaStream.removeTrack(track);
              tracksCleaned++;
            } catch (error) {
              console.error(`Error cleaning up ${track.kind} track:`, error);
            }
          });
          
          console.log('Media stream cleanup completed', {
            tracksCleaned,
            durationMs: Date.now() - cleanupStartTime
          });
        }
        
        videoRef.current.srcObject = null;
        videoRef.current.load();
        console.log('Video element reset');
      } catch (error) {
        console.error('Error cleaning up video element:', error);
      }
    }

    // Reset state
    setRetryCount(0);
    setIsRecovering(false);
    
    console.log('WebRTC cleanup completed', {
      totalDurationMs: Date.now() - cleanupStartTime
    });
  }, [peerConnection]);
  const [overlaySettings, setOverlaySettings] = React.useState<OverlaySettings>({
    title: "",
    logo: "",
    showViewerCount: true,
    customText: "",
    position: "top-left"
  });
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const overlayRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!id) return;

    // Remove old cleanup function since we're using cleanupWebRTCResources

    const fetchStream = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await streams.get(id);
        setStream(response.data);

        const keyResponse = await streams.getStreamKey(id);
        setStreamKey(keyResponse.data.key);
      } catch (error) {
        setError('Failed to load stream data. Please try again.');
        toast({
          description: "Failed to load stream data",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    const connectWebSocket = (): (() => void) => {
      console.log('Initializing WebSocket connection...');
      const newSocket = io(import.meta.env.VITE_WEBSOCKET_URL, {
        query: { streamId: id },
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 10000,
        autoConnect: false
      });

      const handleConnect = () => {
        console.log('Connected to signaling server');
        toast({
          description: "Connected to stream server",
        });
      };

      const handleConnectError = (error: Error) => {
        console.error('WebSocket connection error:', error);
        toast({
          description: "Failed to connect to stream server. Retrying...",
          variant: "destructive",
        });
      };

      const handleReconnect = (attemptNumber: number) => {
        console.log(`Reconnection attempt ${attemptNumber}`);
        toast({
          description: `Reconnecting to server (attempt ${attemptNumber})...`,
        });
      };

      const handleReconnectError = (error: Error) => {
        console.error('WebSocket reconnection failed:', error);
        toast({
          description: "Failed to reconnect. Please refresh the page.",
          variant: "destructive",
        });
        cleanupWebRTCResources();
      };

      newSocket.on("connect", handleConnect);
      newSocket.on("connect_error", handleConnectError);
      newSocket.on("reconnect", handleReconnect);
      newSocket.on("reconnect_error", handleReconnectError);
      newSocket.connect();

      newSocket.on("chat_message", (message: ChatMessage) => {
        setMessages((prev) => [...prev, message]);
      });

      newSocket.on("offer", async (offer: RTCSessionDescriptionInit) => {
        if (!peerConnection) {
          try {
            console.log('Initializing WebRTC connection...');
            const pc = new RTCPeerConnection({
              iceServers: [
                { urls: "stun:stun.l.google.com:19302" },
                { urls: "stun:stun1.l.google.com:19302" },
                { urls: "stun:stun2.l.google.com:19302" },
                { urls: "stun:stun3.l.google.com:19302" },
                { urls: "stun:stun4.l.google.com:19302" }
              ],
              iceCandidatePoolSize: 10,
              bundlePolicy: 'max-bundle',
              rtcpMuxPolicy: 'require',
              iceTransportPolicy: 'all'
            });
            
            pc.ontrack = (event) => {
              if (videoRef.current && event.streams[0]) {
                try {
                  videoRef.current.srcObject = event.streams[0];
                  
                  const playVideo = async (retryCount = 0) => {
                    if (isRecovering) {
                      console.log('Skipping playback attempt during recovery');
                      return;
                    }

                    try {
                      await videoRef.current?.play();
                      setRetryCount(0);
                      toast({
                        description: "Stream playback started",
                      });
                    } catch (error) {
                      console.error('Failed to play video:', error);
                      
                      if (error instanceof DOMException) {
                        switch (error.name) {
                          case 'NotAllowedError':
                            toast({
                              description: "Autoplay blocked. Click the video to start playback.",
                              variant: "destructive"
                            });
                            
                            const clickHandler = async () => {
                              try {
                                if (!isRecovering) {
                                  await videoRef.current?.play();
                                  videoRef.current?.removeEventListener('click', clickHandler);
                                  toast({
                                    description: "Playback started",
                                  });
                                }
                              } catch (playError) {
                                console.error('Click-to-play failed:', playError);
                                if (!isRecovering) {
                                  setIsRecovering(true);
                                  toast({
                                    description: "Playback failed. Attempting to recover stream...",
                                    variant: "destructive"
                                  });
                                  
                                  const recoveryTimeout = setTimeout(() => {
                                    if (isRecovering) {
                                      setIsRecovering(false);
                                      toast({
                                        description: "Stream recovery failed. Please refresh the page.",
                                        variant: "destructive"
                                      });
                                    }
                                  }, RECOVERY_TIMEOUT);
                                  
                                  cleanupWebRTCResources();
                                  connectWebSocket();
                                  
                                  return () => clearTimeout(recoveryTimeout);
                                }
                              }
                            };
                            
                            videoRef.current?.addEventListener('click', clickHandler);
                            break;
                            
                          case 'NotSupportedError':
                            toast({
                              description: "Video format not supported by your browser.",
                              variant: "destructive"
                            });
                            break;
                            
                          case 'AbortError':
                            if (!isRecovering && retryCount < MAX_RETRY_ATTEMPTS) {
                              const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                              setRetryCount(count => count + 1);
                              toast({
                                description: `Playback interrupted. Retrying in ${backoffDelay/1000}s...`,
                                variant: "destructive"
                              });
                              setTimeout(() => playVideo(retryCount + 1), backoffDelay);
                            } else {
                              toast({
                                description: "Failed to start playback. Please refresh the page.",
                                variant: "destructive"
                              });
                            }
                            break;
                            
                          default:
                            if (!isRecovering && retryCount < MAX_RETRY_ATTEMPTS) {
                              const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                              setRetryCount(count => count + 1);
                              toast({
                                description: `Playback failed. Retrying in ${backoffDelay/1000}s...`,
                                variant: "destructive"
                              });
                              setTimeout(() => playVideo(retryCount + 1), backoffDelay);
                            } else {
                              toast({
                                description: "Failed to play stream. Please refresh the page.",
                                variant: "destructive"
                              });
                            }
                        }
                      }
                    }
                  };
                  
                  playVideo();
                } catch (error) {
                  console.error('Failed to set video source:', error);
                  toast({
                    description: "Failed to initialize video player. Please check your browser compatibility.",
                    variant: "destructive"
                  });
                }
              }
            };

            let iceCandidatesCollected = 0;
            const maxIceCandidates = 20; // Reasonable upper limit
            const iceCollectionTimeout = 8000; // 8 seconds timeout
            
            pc.onicecandidate = (event) => {
              if (event.candidate) {
                iceCandidatesCollected++;
                console.log(`ICE candidate collected (${iceCandidatesCollected}/${maxIceCandidates}):`, {
                  type: event.candidate.type,
                  protocol: event.candidate.protocol,
                  address: event.candidate.address,
                  port: event.candidate.port
                });
                
                try {
                  newSocket.emit("ice_candidate", event.candidate);
                } catch (error) {
                  console.error('Failed to send ICE candidate:', error);
                  
                  if (!isRecovering && retryCount < MAX_RETRY_ATTEMPTS) {
                    setIsRecovering(true);
                    const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                    setRetryCount(count => count + 1);
                    
                    toast({
                      description: "Network connection issue detected. Attempting to recover...",
                      variant: "destructive"
                    });
                    
                    setTimeout(() => {
                      if (isRecovering) {
                        cleanupWebRTCResources();
                        connectWebSocket();
                      }
                    }, backoffDelay);
                  } else {
                    toast({
                      description: "Failed to establish network connection. Please check your firewall settings.",
                      variant: "destructive"
                    });
                  }
                }
                
                // Stop collecting if we've reached the maximum
                if (iceCandidatesCollected >= maxIceCandidates) {
                  console.log('Maximum ICE candidates collected');
                  return;
                }
              } else {
                console.log('ICE candidate collection complete');
              }
            };
            
            // Set a timeout for ICE gathering
            const timeoutId = setTimeout(() => {
              if (pc.iceGatheringState !== 'complete' && !isRecovering) {
                console.warn('ICE gathering timed out');
                clearTimeout(timeoutId);
                
                if (iceCandidatesCollected === 0) {
                  toast({
                    description: "Unable to establish network connection. Please check your network settings.",
                    variant: "destructive"
                  });
                  cleanupWebRTCResources();
                } else {
                  console.log(`Proceeding with ${iceCandidatesCollected} ICE candidates`);
                }
              }
            }, iceCollectionTimeout);

            let lastIceState = pc.iceConnectionState;
            let stateChangeTime = Date.now();
            
            pc.oniceconnectionstatechange = () => {
              const state = pc.iceConnectionState;
              const stateTransitionTime = Date.now() - stateChangeTime;
              
              console.log('ICE connection state change:', {
                from: lastIceState,
                to: state,
                transitionTimeMs: stateTransitionTime,
                retryCount,
                isRecovering
              });
              
              stateChangeTime = Date.now();
              lastIceState = state;
              
              switch (state) {
                case 'checking':
                  if (!isRecovering) {
                    toast({
                      description: "Establishing network connection...",
                    });
                  }
                  break;
                  
                case 'failed':
                  console.error('ICE connection failed', {
                    retryCount,
                    isRecovering,
                    connectionState: pc.connectionState,
                    signalingState: pc.signalingState
                  });
                  
                  if (!isRecovering && retryCount < MAX_RETRY_ATTEMPTS) {
                    setIsRecovering(true);
                    const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                    
                    toast({
                      description: `Connection failed. Retrying in ${backoffDelay/1000}s...`,
                      variant: "destructive"
                    });
                    
                    const recoveryTimeout = setTimeout(() => {
                      if (isRecovering) {
                        setIsRecovering(false);
                        toast({
                          description: "Connection recovery timed out. Please check your network and refresh.",
                          variant: "destructive"
                        });
                      }
                    }, RECOVERY_TIMEOUT);
                    
                    setTimeout(() => {
                      if (isRecovering) {
                        console.log('Attempting connection recovery...', {
                          backoffDelay,
                          retryCount: retryCount + 1
                        });
                        cleanupWebRTCResources();
                        connectWebSocket();
                      }
                    }, backoffDelay);
                    
                    return () => clearTimeout(recoveryTimeout);
                  }
                  break;
                  
                case 'disconnected':
                  if (!isRecovering && retryCount < MAX_RETRY_ATTEMPTS) {
                    setIsRecovering(true);
                    const reconnectDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                    
                    console.log('Connection interrupted', {
                      reconnectDelay,
                      retryCount: retryCount + 1
                    });
                    
                    toast({
                      description: "Connection interrupted. Attempting to recover...",
                      variant: "destructive"
                    });
                    
                    setTimeout(() => {
                      if (isRecovering && pc.iceConnectionState === 'disconnected') {
                        cleanupWebRTCResources();
                        connectWebSocket();
                      }
                    }, reconnectDelay);
                  }
                  break;
                  
                case 'connected':
                  console.log('ICE connection established', {
                    setupTimeMs: Date.now() - stateChangeTime,
                    candidates: iceCandidatesCollected
                  });
                  
                  setIsRecovering(false);
                  setRetryCount(0);
                  toast({
                    description: "Network connection established",
                  });
                  break;
                  
                case 'completed':
                  console.log('ICE connection completed', {
                    setupTimeMs: Date.now() - stateChangeTime,
                    candidates: iceCandidatesCollected
                  });
                  break;
              }
            };

            let gatheringStartTime = Date.now();
            const MAX_GATHERING_TIME = 12000; // 12 seconds
            
            pc.onicegatheringstatechange = () => {
              const state = pc.iceGatheringState;
              const gatheringTime = Date.now() - gatheringStartTime;
              
              console.log('ICE gathering state change:', {
                state,
                gatheringTimeMs: gatheringTime,
                candidates: iceCandidatesCollected,
                connectionState: pc.connectionState,
                signalingState: pc.signalingState
              });
              
              switch (state) {
                case 'gathering':
                  gatheringStartTime = Date.now();
                  
                  if (!isRecovering) {
                    toast({
                      description: "Finding optimal connection route...",
                    });
                    
                    const gatheringTimeout = setTimeout(() => {
                      const currentGatheringTime = Date.now() - gatheringStartTime;
                      
                      if (pc.iceGatheringState === 'gathering' && !isRecovering) {
                        console.error('ICE gathering timed out', {
                          gatheringTimeMs: currentGatheringTime,
                          candidates: iceCandidatesCollected
                        });
                        
                        if (iceCandidatesCollected === 0) {
                          toast({
                            description: "No network routes found. Please check your connection.",
                            variant: "destructive"
                          });
                          cleanupWebRTCResources();
                        } else if (retryCount < MAX_RETRY_ATTEMPTS) {
                          setIsRecovering(true);
                          const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                          setRetryCount(count => count + 1);
                          
                          toast({
                            description: `Connection setup taking too long. Retrying in ${backoffDelay/1000}s...`,
                            variant: "destructive"
                          });
                          
                          const recoveryTimeout = setTimeout(() => {
                            if (isRecovering) {
                              setIsRecovering(false);
                              toast({
                                description: "Connection setup failed. Please refresh the page.",
                                variant: "destructive"
                              });
                            }
                          }, RECOVERY_TIMEOUT);
                          
                          setTimeout(() => {
                            if (isRecovering) {
                              console.log('Restarting connection after gathering timeout', {
                                backoffDelay,
                                retryCount: retryCount + 1,
                                candidates: iceCandidatesCollected
                              });
                              cleanupWebRTCResources();
                              connectWebSocket();
                            }
                          }, backoffDelay);
                          
                          return () => clearTimeout(recoveryTimeout);
                        }
                      }
                    }, MAX_GATHERING_TIME);
                    
                    return () => clearTimeout(gatheringTimeout);
                  }
                  break;
                  
                case 'complete':
                  const finalGatheringTime = Date.now() - gatheringStartTime;
                  console.log('ICE gathering completed', {
                    durationMs: finalGatheringTime,
                    candidates: iceCandidatesCollected,
                    connectionState: pc.connectionState
                  });
                  
                  if (iceCandidatesCollected === 0) {
                    toast({
                      description: "No network routes found. Please check your connection.",
                      variant: "destructive"
                    });
                    cleanupWebRTCResources();
                  } else if (pc.connectionState === 'new' || pc.connectionState === 'connecting') {
                    toast({
                      description: "Connection routes found, establishing connection...",
                    });
                  } else if (!isRecovering && (pc.connectionState === 'disconnected' || pc.connectionState === 'failed')) {
                    setIsRecovering(true);
                    const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                    setRetryCount(count => count + 1);
                    
                    console.error('ICE gathering completed but connection failed', {
                      gatheringTimeMs: finalGatheringTime,
                      candidates: iceCandidatesCollected
                    });
                    
                    toast({
                      description: `Connection unstable. Retrying in ${backoffDelay/1000}s...`,
                      variant: "destructive"
                    });
                    
                    const recoveryTimeout = setTimeout(() => {
                      if (isRecovering) {
                        setIsRecovering(false);
                        toast({
                          description: "Connection recovery failed. Please refresh the page.",
                          variant: "destructive"
                        });
                      }
                    }, RECOVERY_TIMEOUT);
                    
                    setTimeout(() => {
                      if (isRecovering) {
                        cleanupWebRTCResources();
                        connectWebSocket();
                      }
                    }, backoffDelay);
                    
                    return () => clearTimeout(recoveryTimeout);
                  }
                  break;
                  
                case 'new':
                  console.log('Starting new ICE gathering session');
                  break;
              }
            };

            let connectionStartTime = Date.now();
            
            pc.onconnectionstatechange = () => {
              const newState = pc.connectionState;
              const stateTransitionTime = Date.now() - connectionStartTime;
              setConnectionState(newState);
              
              console.log('Connection state changed:', {
                state: newState,
                transitionTimeMs: stateTransitionTime,
                iceState: pc.iceConnectionState,
                signalingState: pc.signalingState,
                retryCount,
                isRecovering
              });
              
              connectionStartTime = Date.now();
              
              switch (newState) {
                case "failed":
                  console.error('Connection failed', {
                    iceState: pc.iceConnectionState,
                    signalingState: pc.signalingState,
                    candidates: iceCandidatesCollected
                  });
                  
                  if (!isRecovering && retryCount < MAX_RETRY_ATTEMPTS) {
                    setIsRecovering(true);
                    const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                    setRetryCount(count => count + 1);
                    
                    toast({
                      description: `Stream connection failed. Retrying in ${backoffDelay/1000}s...`,
                      variant: "destructive",
                    });
                    
                    const recoveryTimeout = setTimeout(() => {
                      if (isRecovering) {
                        setIsRecovering(false);
                        toast({
                          description: "Connection recovery timed out. Please refresh the page.",
                          variant: "destructive"
                        });
                      }
                    }, RECOVERY_TIMEOUT);
                    
                    setTimeout(() => {
                      if (isRecovering) {
                        console.log('Attempting connection recovery', {
                          backoffDelay,
                          retryCount: retryCount + 1,
                          candidates: iceCandidatesCollected
                        });
                        cleanupWebRTCResources();
                        connectWebSocket();
                      }
                    }, backoffDelay);
                    
                    return () => clearTimeout(recoveryTimeout);
                  } else {
                    console.log('Max retry attempts reached or already recovering', {
                      retryCount,
                      isRecovering
                    });
                    
                    toast({
                      description: "Connection failed. Please check your network and refresh.",
                      variant: "destructive"
                    });
                    cleanupWebRTCResources();
                  }
                  break;
                  
                case "disconnected":
                  if (!isRecovering && retryCount < MAX_RETRY_ATTEMPTS) {
                    setIsRecovering(true);
                    const reconnectDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                    setRetryCount(count => count + 1);
                    
                    console.log('Connection interrupted', {
                      reconnectDelay,
                      retryCount: retryCount + 1,
                      iceState: pc.iceConnectionState
                    });
                    
                    toast({
                      description: `Stream connection lost. Reconnecting in ${reconnectDelay/1000}s...`,
                      variant: "destructive"
                    });
                    
                    setTimeout(() => {
                      if (isRecovering && pc.connectionState === 'disconnected') {
                        cleanupWebRTCResources();
                        connectWebSocket();
                      }
                    }, reconnectDelay);
                  }
                  break;
                  
                case "connected":
                  console.log('Connection established', {
                    setupTimeMs: Date.now() - connectionStartTime,
                    candidates: iceCandidatesCollected,
                    iceState: pc.iceConnectionState
                  });
                  
                  setRetryCount(0);
                  setIsRecovering(false);
                  toast({
                    description: "Connected to stream",
                  });
                  break;
                  
                case "connecting":
                  console.log('Connection attempt started', {
                    iceState: pc.iceConnectionState,
                    signalingState: pc.signalingState
                  });
                  
                  toast({
                    description: "Establishing connection...",
                  });
                  break;

                case "closed":
                  console.log("Connection closed", {
                    iceState: pc.iceConnectionState,
                    signalingState: pc.signalingState
                  });
                  cleanupWebRTCResources();
                  break;
              }
            };

            const negotiationStartTime = Date.now();
            let currentStep = 'starting';
            
            try {
              console.log('Starting WebRTC negotiation...', {
                iceConnectionState: pc.iceConnectionState,
                iceGatheringState: pc.iceGatheringState,
                connectionState: pc.connectionState,
                signalingState: pc.signalingState,
                retryCount,
                isRecovering
              });

              currentStep = 'setRemoteDescription';
              console.log('Setting remote description...');
              await pc.setRemoteDescription(offer);
              
              currentStep = 'createAnswer';
              console.log('Creating answer...');
              const answer = await pc.createAnswer({
                offerToReceiveAudio: true,
                offerToReceiveVideo: true,
                voiceActivityDetection: true
              });
              
              currentStep = 'setLocalDescription';
              console.log('Setting local description...');
              await pc.setLocalDescription(answer);
              
              currentStep = 'sendAnswer';
              console.log('Sending answer to signaling server...');
              newSocket.emit("answer", answer);
              
              const negotiationTime = Date.now() - negotiationStartTime;
              console.log('WebRTC negotiation completed', {
                durationMs: negotiationTime,
                iceState: pc.iceConnectionState,
                connectionState: pc.connectionState,
                signalingState: pc.signalingState
              });
            } catch (error) {
              const negotiationTime = Date.now() - negotiationStartTime;
              console.error('WebRTC negotiation failed', {
                step: currentStep,
                durationMs: negotiationTime,
                error,
                iceState: pc.iceConnectionState,
                connectionState: pc.connectionState,
                signalingState: pc.signalingState,
                retryCount,
                isRecovering
              });
              
              if (!isRecovering && retryCount < MAX_RETRY_ATTEMPTS) {
                setIsRecovering(true);
                const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), BACKOFF_MAX_DELAY);
                setRetryCount(count => count + 1);
                
                console.log('Initiating connection recovery', {
                  step: currentStep,
                  backoffDelay,
                  retryCount: retryCount + 1
                });
                
                toast({
                  description: `Connection setup failed at ${currentStep}. Retrying in ${backoffDelay/1000}s...`,
                  variant: "destructive"
                });
                
                const recoveryTimeout = setTimeout(() => {
                  if (isRecovering) {
                    console.log('Connection recovery timed out', {
                      step: currentStep,
                      retryCount
                    });
                    
                    setIsRecovering(false);
                    toast({
                      description: "Connection setup failed. Please refresh the page.",
                      variant: "destructive"
                    });
                  }
                }, RECOVERY_TIMEOUT);
                
                setTimeout(() => {
                  if (isRecovering) {
                    console.log('Attempting connection recovery', {
                      step: currentStep,
                      backoffDelay,
                      retryCount: retryCount + 1
                    });
                    cleanupWebRTCResources();
                    connectWebSocket();
                  }
                }, backoffDelay);
                
                return () => clearTimeout(recoveryTimeout);
              } else {
                console.log('Max retry attempts reached or already recovering', {
                  step: currentStep,
                  retryCount,
                  isRecovering
                });
                
                toast({
                  description: "Failed to establish media connection. Please refresh and try again.",
                  variant: "destructive"
                });
                cleanupWebRTCResources();
                throw error;
              }
            }
            
            setPeerConnection(pc);
          } catch (error) {
            console.error("WebRTC setup error:", error);
            toast({
              title: "Connection Error",
              description: "Failed to establish stream connection",
              variant: "destructive",
            });
          }
        }
      });

      newSocket.on("ice_candidate", async (candidate: RTCIceCandidate) => {
        if (peerConnection) {
          await peerConnection.addIceCandidate(candidate);
        }
      });

      setSocket(newSocket);

      return () => {
        newSocket.disconnect();
        setSocket(null);
      };
    };

    let socketCleanup: (() => void) | undefined;
    
    const initializeStream = async () => {
      try {
        await fetchStream();
        socketCleanup = connectWebSocket();
      } catch (error) {
        console.error('Failed to initialize stream:', error);
        toast({
          description: "Failed to initialize stream. Please try again.",
          variant: "destructive"
        });
      }
    };

    initializeStream();

    return () => {
      if (socket) {
        // Cleanup all socket event listeners
        socket.off("connect");
        socket.off("connect_error");
        socket.off("reconnect");
        socket.off("reconnect_error");
        socket.off("disconnect");
        socket.off("chat_message");
        socket.off("offer");
        socket.off("ice_candidate");
        
        // Force close the socket connection
        socket.disconnect();
        socket.close();
      }
      
      // Cleanup WebRTC resources
      cleanupWebRTCResources();
      socketCleanup?.();
    };
  }, [id]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !newMessage.trim()) return;

    try {
      await chat.send(id, newMessage);
      setNewMessage("");
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send message",
        variant: "destructive"
      });
    }
  };

  const copyStreamKey = () => {
    navigator.clipboard.writeText(streamKey);
    toast({
      title: "Success",
      description: "Stream key copied to clipboard"
    });
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading stream...</p>
      </div>
    );
  }

  if (error || !stream) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-destructive">{error || 'Stream not found'}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto grid gap-6 p-6 lg:grid-cols-[1fr,300px]">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">{stream.title}</h1>
          <div className="flex gap-2">
            {canSendSuperChat(id!) && (
              <Button variant="outline" onClick={() => setShowSuperChat(true)}>
                Super Chat
              </Button>
            )}
            {hasStreamPermission(id!, 'edit') && (
              <>
                <Button variant="outline" onClick={() => setShowAnalytics(!showAnalytics)}>
                  <BarChart className="mr-2 h-4 w-4" />
                  Analytics
                </Button>
                <Button variant="outline" size="icon" onClick={() => setShowSettings(true)}>
                  <Settings className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="aspect-video rounded-lg bg-black">
          {stream.status === 'live' ? (
            <div className="relative">
              {(connectionState === 'connecting' || connectionState === 'new') && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <p className="text-white">Connecting to stream...</p>
                </div>
              )}
              <video
                ref={videoRef}
                className="h-full w-full"
                controls
                autoPlay
                playsInline
              />
              <div
                ref={overlayRef}
                className={`absolute p-4 ${
                  overlaySettings.position === "top-left" ? "top-0 left-0" :
                  overlaySettings.position === "top-right" ? "top-0 right-0" :
                  overlaySettings.position === "bottom-left" ? "bottom-0 left-0" :
                  "bottom-0 right-0"
                } bg-black/50`}
              >
                {overlaySettings.logo && (
                  <img src={overlaySettings.logo} alt="Stream Logo" className="h-12 w-12 mb-2" />
                )}
                {overlaySettings.title && (
                  <h3 className="text-white text-lg font-bold">{overlaySettings.title}</h3>
                )}
                {overlaySettings.customText && (
                  <p className="text-white">{overlaySettings.customText}</p>
                )}
                {overlaySettings.showViewerCount && (
                  <p className="text-white text-sm">{formatViewCount(stream.viewerCount)} viewers</p>
                )}
              </div>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center">
              <p className="text-muted-foreground">Stream is not live</p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="text-muted-foreground">
              {formatViewCount(stream.viewerCount)} viewers
            </p>
            {stream.description && (
              <p className="mt-2 text-muted-foreground">{stream.description}</p>
            )}
          </div>
        </div>

        {showAnalytics && (
          <StreamAnalytics streamId={id!} />
        )}

        <Dialog open={showSettings} onOpenChange={setShowSettings}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Stream Settings</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="stream-key">Stream Key</Label>
                <div className="flex gap-2">
                  <Input id="stream-key" type="password" value={streamKey} readOnly />
                  <Button variant="outline" size="icon" onClick={copyStreamKey}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Use this key in your streaming software (e.g., OBS Studio)
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="rtmp-url">RTMP URL</Label>
                <Input
                  id="rtmp-url"
                  value={`rtmp://${import.meta.env.VITE_API_URL}/live`}
                  readOnly
                />
              </div>
              <div className="border-t pt-4 space-y-4">
                <h3 className="font-medium">Stream Overlay</h3>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="title-overlay">Title Overlay</Label>
                    <Input
                      id="title-overlay"
                      value={overlaySettings.title}
                      onChange={(e) => setOverlaySettings(prev => ({ ...prev, title: e.target.value }))}
                      placeholder="Stream Title Overlay"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="custom-text">Custom Text</Label>
                    <Input
                      id="custom-text"
                      value={overlaySettings.customText}
                      onChange={(e) => setOverlaySettings(prev => ({ ...prev, customText: e.target.value }))}
                      placeholder="Additional overlay text"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="logo-url">Logo URL</Label>
                    <Input
                      id="logo-url"
                      value={overlaySettings.logo}
                      onChange={(e) => setOverlaySettings(prev => ({ ...prev, logo: e.target.value }))}
                      placeholder="Logo image URL"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="show-viewer-count">Show Viewer Count</Label>
                    <Switch
                      id="show-viewer-count"
                      checked={overlaySettings.showViewerCount}
                      onCheckedChange={(checked) =>
                        setOverlaySettings((prev) => ({
                          ...prev,
                          showViewerCount: checked,
                        }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Position</Label>
                    <Select
                      value={overlaySettings.position}
                      onValueChange={(value: OverlayPosition) =>
                        setOverlaySettings((prev) => ({
                          ...prev,
                          position: value,
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select position" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="top-left">Top Left</SelectItem>
                        <SelectItem value="top-right">Top Right</SelectItem>
                        <SelectItem value="bottom-left">Bottom Left</SelectItem>
                        <SelectItem value="bottom-right">Bottom Right</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <SuperChatDialog
          streamId={id!}
          open={showSuperChat}
          onOpenChange={setShowSuperChat}
        />
      </div>

      <Card className="h-[calc(100vh-2rem)]">
        <CardHeader>
          <CardTitle>Live Chat</CardTitle>
        </CardHeader>
        <CardContent className="flex h-full flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto">
            {messages.map((message) => (
              <div key={message.id} className="space-y-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{message.username}</p>
                  {message.type === 'super_chat' && message.amount && (
                    <span className="rounded bg-yellow-500/10 px-1.5 py-0.5 text-xs text-yellow-500">
                      Super Chat ${message.amount.toFixed(2)}
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  {message.content}
                </p>
              </div>
            ))}
          </div>
          <form onSubmit={handleSendMessage} className="mt-4 flex gap-2">
            <Input
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type a message..."
            />
            <Button type="submit">Send</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
