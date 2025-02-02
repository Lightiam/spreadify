from typing import List, Dict, Optional
import ffmpeg_streaming
from ffmpeg_streaming import Formats, Representation, Size, Bitrate
import asyncio
import os
from pathlib import Path

class VideoProcessor:
    def __init__(self):
        self.output_dir = Path("uploads/streams")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def create_hls_stream(
        self,
        input_url: str,
        stream_id: str,
        qualities: List[Dict[str, int]] = None
    ) -> str:
        if qualities is None:
            qualities = [
                {"height": 1080, "bitrate": 6000},  # 1080p
                {"height": 720, "bitrate": 4000},   # 720p
                {"height": 480, "bitrate": 2000},   # 480p
                {"height": 360, "bitrate": 1000}    # 360p
            ]
        
        output_path = self.output_dir / f"{stream_id}"
        output_path.mkdir(exist_ok=True)
        
        video = ffmpeg_streaming.input(input_url)
        
        hls = video.hls(Formats.h264())
        representations = []
        
        for quality in qualities:
            representations.append(
                Representation(
                    Size(height=quality["height"]),
                    Bitrate(quality["bitrate"], 128)  # Video bitrate, Audio bitrate
                )
            )
        
        hls.representations(*representations)
        hls.output(str(output_path / "stream.m3u8"), async_run=True)
        
        return f"/uploads/streams/{stream_id}/stream.m3u8"
    
    async def create_dash_stream(
        self,
        input_url: str,
        stream_id: str,
        qualities: List[Dict[str, int]] = None
    ) -> str:
        if qualities is None:
            qualities = [
                {"height": 1080, "bitrate": 6000},
                {"height": 720, "bitrate": 4000},
                {"height": 480, "bitrate": 2000},
                {"height": 360, "bitrate": 1000}
            ]
        
        output_path = self.output_dir / f"{stream_id}"
        output_path.mkdir(exist_ok=True)
        
        video = ffmpeg_streaming.input(input_url)
        
        dash = video.dash(Formats.h264())
        representations = []
        
        for quality in qualities:
            representations.append(
                Representation(
                    Size(height=quality["height"]),
                    Bitrate(quality["bitrate"], 128)
                )
            )
        
        dash.representations(*representations)
        dash.output(str(output_path / "stream.mpd"), async_run=True)
        
        return f"/uploads/streams/{stream_id}/stream.mpd"
    
    async def process_stream(
        self,
        input_url: str,
        stream_id: str,
        format: str = "hls",
        qualities: Optional[List[Dict[str, int]]] = None
    ) -> str:
        if format.lower() == "hls":
            return await self.create_hls_stream(input_url, stream_id, qualities)
        elif format.lower() == "dash":
            return await self.create_dash_stream(input_url, stream_id, qualities)
        else:
            raise ValueError("Unsupported format. Use 'hls' or 'dash'.")
    
    async def cleanup_stream(self, stream_id: str):
        stream_path = self.output_dir / f"{stream_id}"
        if stream_path.exists():
            for file in stream_path.glob("*"):
                file.unlink()
            stream_path.rmdir()
