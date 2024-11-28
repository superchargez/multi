import json
from pathlib import Path
from datetime import datetime
import shutil
import os
from openai import OpenAI
from typing import Dict, List
import fitz
from PIL import Image
import base64
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from prompts4 import system_prompt1, instruction6
from prompt_function import create_prompt
from dotenv import load_dotenv

system_prompt, instruction = system_prompt1, instruction6
dotenv_path = os.path.expanduser("~/.env")

# Load the environment variables from the specified file
load_dotenv(dotenv_path)

# api_key = os.getenv('OAI_KEY')
# if not api_key:
#     raise ValueError("OAI_KEY environment variable not set")
# client = OpenAI(api_key=api_key)
client = OpenAI()
output_dir = Path("../savings/mid")
output_dir.mkdir(parents=True, exist_ok=True)

def initialize_job(jobs: dict, job_id: str):
    """Initialize job status in the jobs dictionary."""
    jobs[job_id] = {"status": "in_progress", "message": "Processing started"}

def update_job_status(jobs: dict, job_id: str, status: str, message: str):
    """Update job status in the jobs dictionary."""
    jobs[job_id] = {
        "status": status,
        "message": message,
        "file_paths": {str(k): str(v) for k, v in get_file_paths(job_id).items()}
    }

def get_file_paths(job_id: str) -> dict[str, Path]:
    """Get all file paths for a job ID."""
    return {
        'markdown': output_dir / f"{job_id}.md",
        'json': output_dir / f"{job_id}.json",
        'metadata': output_dir / f"{job_id}.meta.json",
        'pages_dir': output_dir / job_id
    }

def save_job_metadata(job_id: str, original_filename: str):
    """Save job metadata including original filename."""
    paths = get_file_paths(job_id)
    metadata = {
        "original_filename": original_filename,
        "created_at": datetime.utcnow().isoformat(),
        "job_id": job_id
    }
    with paths['metadata'].open('w') as f:
        json.dump(metadata, f)

def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def analyze_image_sync(base64_image: str, page_num: int, job_id: str) -> tuple[str, Path]:
    """Synchronous version of image analysis."""
    paths = get_file_paths(job_id)
    paths['pages_dir'].mkdir(exist_ok=True)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        
        page_md_path = paths['pages_dir'] / f"page_{page_num}.md"
        with page_md_path.open('w', encoding='utf-8') as f:
            f.write(content)
        
        return content, page_md_path
    except Exception as e:
        print(f"Error analyzing page {page_num}: {str(e)}")
        raise

def gpt4o_mini_analyze_sync(content: str, page_num: int, job_id: str) -> Dict:
    """Synchronous version of GPT-4 analysis."""
    paths = get_file_paths(job_id)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": create_prompt(content, page_num)}
            ],
            temperature=0.0,
        )
        
        content = response.choices[0].message.content
        content = content.strip("```json\n").strip("```").replace("\\n", "")
        json_output = json.loads(content)
        
        page_json_path = paths['pages_dir'] / f"page_{page_num}.json"
        with page_json_path.open('w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2)
        
        return json_output
    except Exception as e:
        print(f"Error analyzing page {page_num}: {str(e)}")
        return {"error": str(e), "page_number": page_num}

def sync_process_pdf(pdf_path: str, job_id: str) -> int:
    """Synchronous version of PDF processing, returns number of pages."""
    paths = get_file_paths(job_id)
    page_count = 0

    try:
        paths['pages_dir'].mkdir(exist_ok=True)
        
        # Convert PDF to images
        doc = fitz.open(pdf_path)
        page_count = len(doc)  # Store the number of pages for later use
        images = []
        
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        
        all_contents = []
        all_analyses = []
        
        # Process each page
        with ThreadPoolExecutor() as local_executor:
            base64_images = list(local_executor.map(image_to_base64, images))
        
        for i, base64_img in enumerate(base64_images):
            content, _ = analyze_image_sync(base64_img, i + 1, job_id)
            all_contents.append(f"## Page {i + 1}\n{content}\n")
            analysis = gpt4o_mini_analyze_sync(content, i + 1, job_id)
            all_analyses.append(analysis)
        
        with paths['markdown'].open('w', encoding='utf-8') as f:
            f.writelines(all_contents)
        
        with paths['json'].open('w', encoding='utf-8') as f:
            json.dump(all_analyses, f, ensure_ascii=False, indent=2)
        
        return page_count  # Return the page count for wait logic
        
    except Exception as e:
        print(f"Error in sync_process_pdf: {str(e)}")
        for path in paths.values():
            if isinstance(path, Path) and path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        raise
    finally:
        if isinstance(doc, fitz.Document):
            doc.close()
