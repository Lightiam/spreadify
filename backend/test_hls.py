import asyncio
import logging
from app.services.video_processor import VideoProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test():
    try:
        logger.info("Initializing VideoProcessor")
        vp = VideoProcessor()
        
        logger.info("Starting HLS stream processing")
        output_url = await vp.process_stream(
            input_url='uploads/streams/test/test_input.mp4',
            stream_id='test_hls',
            overlays=[{
                'path': 'uploads/streams/test/test_overlay.png',
                'position_x': 10,
                'position_y': 10,
                'scale': 1.0
            }],
            format='hls'
        )
        
        logger.info(f"Stream processing completed. Output URL: {output_url}")
        
        # List generated files
        import os
        logger.info("Generated files:")
        for root, dirs, files in os.walk('uploads/streams/test_hls'):
            for file in files:
                logger.info(f"- {os.path.join(root, file)}")
                
    except Exception as e:
        logger.error(f"Error during stream processing: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(test())
