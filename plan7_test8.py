from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
import shutil
from rich import print
import json
from pathlib import Path
import uuid
import asyncio
from concurrent.futures import ProcessPoolExecutor
import markdown2
from prompts4 import system_prompt1, instruction6
system_prompt, instruction = system_prompt1, instruction6

from functions2import2 import (
    get_file_paths, save_job_metadata, sync_process_pdf,
    initialize_job, update_job_status
)

# Initialize ProcessPoolExecutor
executor = ProcessPoolExecutor()
jobs = {}

app = FastAPI()
from analysis_endpoints import router as analysis_router
app.include_router(analysis_router, tags=['analysis'])

base_dir = Path(__file__).resolve().parent
# print(f"TEMP BASE {base_dir}")
output_dir = (base_dir / "../savings/mid").resolve()
output_dir.mkdir(parents=True, exist_ok=True)
# print(f"Resolved Output Directory: {output_dir}")

temp_dir = (base_dir / "../savings/temp").resolve()
temp_dir.mkdir(parents=True, exist_ok=True)
# print(f"Resolved Temp Directory: {temp_dir}")

# Create an async process_pdf wrapper
async def process_in_background(pdf_path: Path, job_id: str):
    try:
        # Initialize job status
        initialize_job(jobs, job_id)
        
        # Run the synchronous processing function in the process pool
        await asyncio.get_event_loop().run_in_executor(
            executor,
            sync_process_pdf,
            str(pdf_path),
            job_id
        )
        
        # Update job status on completion
        update_job_status(jobs, job_id, "completed", "Processing completed successfully")
        
    except Exception as e:
        print(f"Error in process_in_background: {str(e)}")
        update_job_status(jobs, job_id, "failed", str(e))
        if pdf_path.exists():
            pdf_path.unlink()
        raise

@app.post("/upload/")
async def upload_pdf(file: UploadFile):
    job_id = str(uuid.uuid4())
    pdf_path = temp_dir / f"{job_id}.pdf"
    
    try:
        with pdf_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        save_job_metadata(job_id, file.filename)
        # Start async processing
        asyncio.create_task(process_in_background(pdf_path, job_id))
        return {"message": "File uploaded successfully, processing started.", "job_id": job_id}
    except Exception as e:
        print(f"Error in upload_pdf: {str(e)}")
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/markdown/{job_id}")
async def get_markdown_result(job_id: str, page: int = None):
    paths = get_file_paths(job_id)
    
    # Check job status first
    job_status = jobs.get(job_id)
    if job_status and job_status["status"] == "in_progress":
        return JSONResponse(
            status_code=202,
            content={"status": "pending", "message": "Processing in progress"}
        )
    elif job_status and job_status["status"] == "failed":
        raise HTTPException(status_code=500, detail=job_status["message"])
    
    try:
        if page is not None:
            page_path = paths['pages_dir'] / f"page_{page}.md"
            if not page_path.exists():
                raise HTTPException(status_code=404, detail=f"Page {page} not found")
            markdown_path = page_path
        else:
            if not paths['markdown'].exists():
                raise HTTPException(status_code=404, detail="Processed results not found")
            markdown_path = paths['markdown']
        
        # Read file asynchronously
        async def read_file():
            return await asyncio.to_thread(markdown_path.read_text, encoding='utf-8')
            
        markdown_content = await read_file()
        html_content = await asyncio.to_thread(markdown2.markdown, markdown_content)
        
        styled_html = f"""
        <html>
        <head>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/4.0.0/github-markdown.min.css">
            <style>
                .markdown-body {{
                    box-sizing: border-box;
                    min-width: 200px;
                    max-width: 980px;
                    margin: 0 auto;
                    padding: 45px;
                }}
            </style>
        </head>
        <body>
            <article class="markdown-body">
                {html_content}
            </article>
        </body>
        </html>
        """
        return HTMLResponse(content=styled_html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading markdown: {str(e)}")

@app.get("/result/{job_id}")
async def get_result(job_id: str, page: int = None):
    paths = get_file_paths(job_id)
    
    # Check job status first
    job_status = jobs.get(job_id)
    if job_status and job_status["status"] == "in_progress":
        return JSONResponse(
            status_code=202,
            content={"status": "pending", "message": "Processing in progress"}
        )
    elif job_status and job_status["status"] == "failed":
        return {"status": "failed", "message": job_status["message"]}
    
    try:
        if page is not None:
            page_path = paths['pages_dir'] / f"page_{page}.json"
            if not page_path.exists():
                raise HTTPException(status_code=404, detail=f"Page {page} not found")
            json_path = page_path
        else:
            if not paths['json'].exists():
                raise HTTPException(status_code=404, detail="Processed results not found")
            json_path = paths['json']
        
        # Read JSON file asynchronously
        async def read_json():
            return await asyncio.to_thread(json_path.read_text, encoding='utf-8')
            
        content = await read_json()
        return JSONResponse(content=json.loads(content))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading results: {str(e)}")

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    paths = get_file_paths(job_id)
    
    # Check in-memory job status first
    if job_id in jobs:
        return {
            "job_id": job_id,
            "status": jobs[job_id]["status"],
            "message": jobs[job_id]["message"],
            "file_paths": jobs[job_id].get("file_paths", {})
        }
    
    # Check if files exist for completed jobs asynchronously
    async def check_files():
        return await asyncio.gather(
            asyncio.to_thread(paths['markdown'].exists),
            asyncio.to_thread(paths['json'].exists)
        )
    
    markdown_exists, json_exists = await check_files()
    
    if markdown_exists and json_exists:
        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Processing completed",
            "file_paths": {str(k): str(v) for k, v in paths.items()}
        }
    
    return {
        "job_id": job_id,
        "status": "not_found",
        "message": "Job not found"
    }

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            if job_id in jobs:
                await websocket.send_json({
                    "job_id": job_id,
                    "status": jobs[job_id]["status"],
                    "message": jobs[job_id]["message"],
                    "file_paths": jobs[job_id].get("file_paths", {})
                })
            await asyncio.sleep(1)  # Adjust the sleep time as needed
    except WebSocketDisconnect:
        print(f"Client disconnected from job {job_id}")

### NEW API
import requests
from extended_functions import process_analysis
async def process_in_background_by_id(pdf_path: Path, job_id: str):
    try:
        # Initialize job status
        initialize_job(jobs, job_id)
        
        # Run the synchronous processing function in the process pool and get the page count
        page_count = await asyncio.get_event_loop().run_in_executor(
            executor,
            sync_process_pdf,
            str(pdf_path),
            job_id
        )
        
        # Update job status on completion
        update_job_status(jobs, job_id, "completed", "Processing completed successfully")
        
        # Calculate wait time (10 seconds per page, up to a maximum of 100 checks)
        max_checks = 100
        wait_time_per_page = 10  # seconds
        json_path = output_dir / f"{job_id}.json"

        # Wait for json_path to be created
        for _ in range(min(page_count * wait_time_per_page // 10, max_checks)):
            if json_path.exists():
                # Call process_analysis when JSON file is ready
                await process_analysis(job_id)
                
                # Call patch_id_mappings after process_analysis completes
                patch_id_mappings(job_id)
                break
            await asyncio.sleep(10)
        else:
            print(f"{json_path} not found after waiting, job {job_id}")
        
    except Exception as e:
        print(f"Error in process_in_background_by_id: {str(e)}")
        update_job_status(jobs, job_id, "failed", str(e))
        if pdf_path.exists():
            pdf_path.unlink()
        raise

def patch_id_mappings(job_id: str):
    # Load the mappings file and wrap it in the required "extraction" key
    # mappings_file_path = Path(f"{job_id}_mappings.json")
    mappings_file_path = output_dir / f"{job_id}_mappings.json"
    
    if mappings_file_path.exists():
        with open(mappings_file_path, "r") as f:
            mappings_content = json.load(f)
        
        # Split the mappings content into chunks of 30
        chunk_size = 30 # used to be 30
        chunks = [mappings_content[i:i + chunk_size] for i in range(0, len(mappings_content), chunk_size)]
        
        for chunk in chunks:
            # Wrap each chunk in the "extraction" key
            wrapped_content = {"extraction": chunk}
            
            # Send the PATCH request
            response = requests.post( # used to be patch
                f"https://quantum.mtptest.co.uk/api/ai/data/{job_id}",
                headers={"Content-Type": "application/json"},
                data=json.dumps(wrapped_content)
            )

            # Check response status and content
            if response.status_code == 200:
                print(f"PATCH request successful for job {job_id} with status {response.status_code}")
            else:
                print(f"PATCH request failed for job {job_id} with status {response.status_code}")
                print(f"Response content: {response.content.decode()}")
    else:
        print(f"Mappings file not found for job {job_id}")

@app.post("/send_patch/{job_id}")
async def send_patch(job_id: str):
    # Load the mappings file and wrap it in the required "extraction" key
    mappings_file_path = Path(f"{job_id}_mappings.json")
    
    if not mappings_file_path.exists():
        raise HTTPException(status_code=404, detail="Mappings file not found")

    with open(mappings_file_path, "r") as f:
        mappings_content = json.load(f)
    
    # Split the mappings content into chunks of 30
    chunk_size = 30
    chunks = [mappings_content[i:i + chunk_size] for i in range(0, len(mappings_content), chunk_size)]
    
    responses = []
    for chunk in chunks:
        # Wrap each chunk in the "extraction" key
        wrapped_content = {"extraction": chunk}
        
        # Send the PATCH request
        response = requests.patch(
            f"https://quantum.mtptest.co.uk/api/ai/data/{job_id}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(wrapped_content)
        )

        # Collect response status and content
        responses.append({
            "status_code": response.status_code,
            "content": response.content.decode()
        })

    return {"responses": responses}

temp_dir_ram = Path("/dev/shm") if Path("/dev/shm").exists() else Path("/tmp")
# temp_dir = (base_dir / "../savings/temp").resolve()
@app.post("/data/{id}")
async def process_by_id(id: str):
    details_url = f"http://quantum.mtptest.co.uk/api/ai/data/{id}"
    try:
        response = requests.get(details_url, timeout=20)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    data = response.json().get("data")
    
    if not data or "attachments" not in data:
        raise HTTPException(status_code=400, detail="No attachments found for the given ID")
    
    pdf_url = data["attachments"]["default"][0]["url"]
    if not pdf_url:
        raise HTTPException(status_code=400, detail="PDF URL not found in response")
    
    pdf_path = temp_dir / f"{id}.pdf"
    
    try:
        pdf_response = requests.get(pdf_url, stream=True, timeout=20)
        pdf_response.raise_for_status()
        
        with pdf_path.open("wb") as pdf_file:
            pdf_file.write(pdf_response.content)
        
        asyncio.create_task(process_in_background_by_id(pdf_path, id))
        
        return {"message": "File downloaded and processing started", "job_id": id}
    
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="PDF download timed out")
    except Exception as e:
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))
