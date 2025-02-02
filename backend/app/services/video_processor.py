from typing import List, Dict, Optional, Any
import logging
import asyncio
import os
from pathlib import Path
import subprocess
import json

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.output_dir = Path("uploads/streams")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quality_presets = [
            {
                "name": "1080p",
                "height": 1080,
                "width": 1920,
                "bitrate": "6000k",
                "audio_bitrate": "192k",
                "framerate": 30
            },
            {
                "name": "720p",
                "height": 720,
                "width": 1280,
                "bitrate": "4000k",
                "audio_bitrate": "128k",
                "framerate": 30
            },
            {
                "name": "480p",
                "height": 480,
                "width": 854,
                "bitrate": "2000k",
                "audio_bitrate": "96k",
                "framerate": 30
            },
            {
                "name": "360p",
                "height": 360,
                "width": 640,
                "bitrate": "1000k",
                "audio_bitrate": "64k",
                "framerate": 30
            }
        ]
    async def create_hls_stream(
        self,
        input_url: str,
        stream_id: str,
        overlays: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        output_path = self.output_dir / stream_id
        output_path.mkdir(exist_ok=True)
        
        variant_playlist = "#EXTM3U\n#EXT-X-VERSION:3\n"
        
        for preset in self.quality_presets:
            quality_dir = output_path / preset["name"]
            quality_dir.mkdir(exist_ok=True)
            
            variant_playlist += (
                f'#EXT-X-STREAM-INF:BANDWIDTH={(int(preset["bitrate"][:-1]) * 1000)},'
                f'RESOLUTION={preset["width"]}x{preset["height"]}\n'
                f'{preset["name"]}/playlist.m3u8\n'
            )
            
            try:
                filter_complex = []
                main_stream = "[0:v]scale={w}:{h}[base]".format(
                    w=preset['width'],
                    h=preset['height']
                )
                filter_complex.append(main_stream)
                
                last_output = "base"
                if overlays:
                    for i, overlay in enumerate(overlays):
                        overlay_input = f"[{i+1}:v]"
                        overlay_output = f"[v{i+1}]"
                        filter_complex.append(
                            f"{overlay_input}scale=iw*{overlay['scale']}:-1[scaled{i}];"
                            f"[{last_output}][scaled{i}]overlay="
                            f"x={overlay['position_x']}:y={overlay['position_y']}"
                            f"{overlay_output}"
                        )
                        last_output = f"v{i+1}"
                
                command = ["ffmpeg", "-i", input_url]
                
                if overlays:
                    for overlay in overlays:
                        command.extend(["-i", overlay["path"]])
                
                # Check if input has audio
                has_audio = False
                try:
                    result = subprocess.run(
                        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", input_url],
                        capture_output=True,
                        text=True
                    )
                    has_audio = "audio" in result.stdout
                except Exception as e:
                    logger.warning(f"Failed to check audio streams: {e}")

                command.extend([
                    "-filter_complex", ";".join(filter_complex),
                    "-map", f"[{last_output}]",
                ])

                if has_audio:
                    command.extend([
                        "-map", "0:a",
                        "-c:a", "aac",
                        "-b:a", preset["audio_bitrate"],
                    ])

                command.extend([
                    "-c:v", "libx264",
                    "-b:v", preset["bitrate"],
                    "-r", str(preset["framerate"]),
                    "-preset", "veryfast",
                    "-hls_time", "2",
                    "-hls_list_size", "3",
                    "-hls_flags", "delete_segments+append_list",
                    "-f", "hls",
                    str(quality_dir / "playlist.m3u8")
                ])
                
                logger.info(f"Running FFmpeg command for quality {preset['name']}: {' '.join(command)}")
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    logger.error(f"FFmpeg error for {preset['name']}: {stderr.decode()}")
                    raise RuntimeError(f"FFmpeg failed for quality {preset['name']}")
                
            except Exception as e:
                logger.error(f"Failed to process stream for quality {preset['name']}: {str(e)}")
                raise
        
        with open(output_path / "master.m3u8", "w") as f:
            f.write(variant_playlist)
        
        return f"/uploads/streams/{stream_id}/master.m3u8"
    

    
    async def process_stream(
        self,
        input_url: str,
        stream_id: str,
        overlays: Optional[List[Dict[str, Any]]] = None,
        format: str = "hls"
    ) -> str:
        if format.lower() == "hls":
            return await self.create_hls_stream(input_url, stream_id, overlays)
        else:
            raise ValueError("Only HLS format is currently supported.")
    
    async def cleanup_stream(self, stream_id: str):
        stream_path = self.output_dir / stream_id
        if stream_path.exists():
            # Clean up each quality variant directory
            for preset in self.quality_presets:
                quality_dir = stream_path / preset["name"]
                if quality_dir.exists():
                    for file in quality_dir.glob("*"):
                        try:
                            file.unlink()
                        except Exception as e:
                            print(f"Error deleting file {file}: {e}")
                    try:
                        quality_dir.rmdir()
                    except Exception as e:
                        print(f"Error removing directory {quality_dir}: {e}")
            
            # Clean up master playlist
            try:
                master_playlist = stream_path / "master.m3u8"
                if master_playlist.exists():
                    master_playlist.unlink()
            except Exception as e:
                print(f"Error deleting master playlist: {e}")
            
            # Remove stream directory
            try:
                stream_path.rmdir()
            except Exception as e:
                print(f"Error removing stream directory: {e}")
