from fastapi import APIRouter, HTTPException
from typing import Optional
import asyncio
import json

from extended_functions import (
    process_analysis,
    get_analysis_paths,
    logger
)

router = APIRouter()

@router.get("/analysis/{job_id}")
async def get_analysis(job_id: str, type: Optional[str] = None):
    """
    Get analysis results for a job.
    Optional type parameter can be: metrics, mappings, or analysis (full)
    """
    paths = get_analysis_paths(job_id)
    
    try:
        # Check if analysis exists
        if not paths['analysis'].exists():
            # Try to process it
            try:
                logger.info(f"Starting analysis for job {job_id}")
                await process_analysis(job_id)
            except Exception as e:
                logger.error(f"Error processing analysis for job {job_id}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing analysis: {str(e)}"
                )
        
        # Determine which file to return
        if type == 'metrics':
            file_path = paths['metrics']
        elif type == 'mappings':
            file_path = paths['mappings']
        else:
            file_path = paths['analysis']
        
        # Read and return the appropriate file
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Analysis file not found: {type or 'full'}"
            )
            
        async def read_json():
            return json.loads(await asyncio.to_thread(file_path.read_text))
            
        content = await read_json()
        return content
        
    except Exception as e:
        logger.error(f"Error in get_analysis for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analysis: {str(e)}"
        )

@router.get("/analysis/{job_id}/status")
async def get_analysis_status(job_id: str):
    """Get the status of analysis files for a job."""
    paths = get_analysis_paths(job_id)
    
    status = {
        'job_id': job_id,
        'files': {}
    }
    
    for name, path in paths.items():
        status['files'][name] = {
            'exists': path.exists(),
            'size': path.stat().st_size if path.exists() else 0,
            'modified': path.stat().st_mtime if path.exists() else None
        }
    
    return status

# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# import asyncio
# @router.websocket("/ws/analysis/{job_id}")
# async def websocket_analysis_endpoint(websocket: WebSocket, job_id: str):
#     await websocket.accept()
#     try:
#         while True:
#             status = await get_analysis_status(job_id)
#             await websocket.send_json(status)
#             await asyncio.sleep(1)  # Adjust the sleep time as needed
#     except WebSocketDisconnect:
#         print(f"Client disconnected from analysis job {job_id}")