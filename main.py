from fastapi import FastAPI, UploadFile, HTTPException, File
import importlib, asyncio
from pathlib import Path

# Import the specific endpoint modules
pdf_processor = importlib.import_module("plan7_test6")
pptx_processor = importlib.import_module("pptx_metrics_extraction")

app = FastAPI()

# Include all routes from `plan7_test6.py` and `pptx_metric_extraction.py`
app.include_router(pdf_processor.app.router, prefix="/pdf")
app.include_router(pptx_processor.app.router, prefix="/pptx")

@app.post("/process/")
async def process_file(file: UploadFile = File(...)):
    """
    Main endpoint to process files by their extension.
    Routes the request to the appropriate processor.
    """
    # Determine the file extension
    file_extension = Path(file.filename).suffix.lower()

    if file_extension == ".pdf":
        # Route to the PDF processor
        try:
            # Save the file temporarily
            temp_file_path = Path(f"/tmp/{file.filename}")
            with open(temp_file_path, "wb") as buffer:
                buffer.write(await file.read())

            # Call the PDF processor's logic
            asyncio.create_task(pdf_processor.process_in_background(temp_file_path, temp_file_path.stem))
            return {"message": "PDF processing started", "job_id": temp_file_path.stem}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

    elif file_extension == ".pptx":
        # Route to the PPTX processor
        return await pptx_processor.process_pptx_content(file)

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only .pdf and .pptx are supported.")

@app.get("/")
async def root():
    return {"message": "Welcome to the file processing API. Use /process/ to upload files."}
