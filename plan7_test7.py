from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.responses import JSONResponse, HTMLResponse
from pathlib import Path
import shutil
from rich import print; import os
import base64
import json, requests
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import fitz
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
from prompts4 import system_prompt1, instruction6
import uuid, logging
from prompt_function import create_prompt

# Initialize directories
temp_dir = Path("../savings/temp")
temp_dir.mkdir(exist_ok=True)
output_dir = Path("../savings/output")
output_dir.mkdir(exist_ok=True)
metric_cache = {}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(output_dir / 'processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


app = FastAPI()
load_dotenv()
system_prompt, instruction = system_prompt1, instruction6

# Initialize OpenAI client
api_key = os.getenv('OAI_KEY')
if not api_key:
    raise ValueError("OAI_KEY environment variable not set")
client = OpenAI(api_key=api_key)

def pdf_to_images(pdf_path: str) -> List[Image.Image]:
    """Convert PDF pages to images."""
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
        
    return images

def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    import io
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def analyze_image(base64_image: str, page_num: int) -> Dict:
    """Send image to GPT-4V for analysis."""
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
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.0
        )
    
    content = response.choices[0].message.content.encode('utf-8')  # Encode response for writing
    
    # Create filename based on UUID and page number
    unique_id = uuid.uuid4()
    filename = f"{unique_id}-page_{page_num}.md"
    filepath = output_dir / filename

    # Save response content to markdown file with UTF-8 encoding
    with filepath.open('w', encoding='utf-8') as f:
        f.write(content.decode('utf-8'))  # Decode before writing

    print(f"Analysis result saved to: {filepath}")

    return content.decode('utf-8'), unique_id  # Decode response before returning

def gpt4o_mini_analyze(content: str, page_num: int) -> Dict:
    """Analyze markdown content using GPT-4o-mini and return JSON output."""
    prompt = create_prompt(content, page_num)
    try:
        # Generate response using GPT-4o-mini
        response = client.chat.completions.create(
            # model="gpt-4o-mini",
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
        )
        
        # Parse the response as JSON
        content = response.choices[0].message.content
        content = content.strip("```json\n").strip("```").replace("\\n", "")
        json_output = json.loads(content)

        return json_output
    except json.JSONDecodeError as e:
        print(f"Error analyzing page {page_num}: Invalid JSON response")
        print(f"Raw response: {response.choices[0].message.content}")
        return {"error": "Invalid JSON response", "page_number": page_num}
    except Exception as e:
        print(f"Error analyzing page {page_num}: {str(e)}")
        return {"error": str(e), "page_number": page_num}

def process_markdown_file(filepath: Path, page_num: int) -> Dict:
    """Process a single markdown file and generate JSON analysis."""
    with filepath.open('r', encoding='utf-8') as f:
        content = f.read()
    
    analysis = gpt4o_mini_analyze(content, page_num)
    
    # Save individual JSON file
    json_filename = f"{filepath.stem}.json"
    with (output_dir / json_filename).open('w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"Analysis for page {page_num} saved to: {json_filename}")
    return analysis

async def process_pdf(pdf_path: Path):
    """
    Process the uploaded PDF: convert it to images, analyze each image with GPT-4o,
    and generate markdown and JSON output for each page and the combined document.
    """
    job_id = str(uuid.uuid4())
    
    try:
        temp_dir = Path("temp")
        output_dir = Path("../savings/output")
        temp_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)

        images = pdf_to_images(str(pdf_path))
        all_contents = []
        all_analyses = []

        # Analyze each image and save markdown and JSON
        for i, image in enumerate(images):
            base64_image = image_to_base64(image)
            content, unique_id = analyze_image(base64_image, i + 1)
            all_contents.append(f"## Page {i + 1}\n{content}\n")

            markdown_filepath = output_dir / f"{unique_id}-page_{i + 1}.md"
            with markdown_filepath.open('w', encoding='utf-8') as f:
                f.write(content)

            analysis = process_markdown_file(markdown_filepath, i + 1)
            all_analyses.append(analysis)

        combined_json_filename = f"{job_id}-combined.json"
        combined_json_filepath = output_dir / combined_json_filename
        with combined_json_filepath.open('w', encoding='utf-8') as f:
            json.dump(all_analyses, f, ensure_ascii=False, indent=2)
        logger.info(f"Combined JSON analysis saved to: {combined_json_filepath}")

        # Process the combined JSON data with process_event
        results = []
        # print(all_analyses)
        for event_data in all_analyses:  # Process each event individually
            event_result = process_event(event_data)  # Remove the second argument
            if event_result:
                results.extend(event_result)

        # Save the final results
        final_results_filename = f"{job_id}-final-results.json"
        final_results_filepath = output_dir / final_results_filename
        with final_results_filepath.open('w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Final results saved to: {final_results_filepath}")

        # Clean up
        pdf_path.unlink()

        return job_id

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        return {"error": str(e), "job_id": job_id}
# starting full code.
def extract_metrics(event_data):
    """Extract metrics from event data with improved logging."""
    metrics = {}
    logger.info("Starting metric extraction")
    logger.info(f"Event data structure: {json.dumps(event_data, indent=2)}")

    def process_dict(data, path="root"):
        for key, value in data.items():
            current_path = f"{path}.{key}"
            if isinstance(value, dict):
                if 'metric_name' in value and 'minValue' in value:
                    metrics[value['metric_name']] = value
                    logger.info(f"Found metric at {current_path}: {value['metric_name']}")
                else:
                    process_dict(value, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        process_dict(item, f"{current_path}[{i}]")

    if isinstance(event_data, dict):
        if 'metrics' in event_data:
            logger.info("Found 'metrics' key in event data")
            process_dict(event_data['metrics'])
        elif 'Statistics' in event_data:
            logger.info("Found 'Statistics' key in event data")
            process_dict(event_data['Statistics'])
        else:
            logger.info("No 'metrics' or 'Statistics' key found, processing entire event data")
            process_dict(event_data)
    
    logger.info(f"Extraction complete. Found {len(metrics)} metrics: {list(metrics.keys())}")
    return metrics

def search_metric(metric_name: str):
    """
    Search for a metric using its name. The function contacts the external service to find the metric details.
    """
    try:
        logger.info(f"Searching for metric: {metric_name}")
        url = f"https://quantum.mtptest.co.uk/api/embeddings/Metric?q={metric_name.replace(' ', '+')}&compact=true&select=name&taxonomy=event&limit=1&threshold=0.4"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            metric = data['data'][0]
            logger.info(f"Metric found: {metric['name']} (ID: {metric['id']})")
            return metric
        else:
            logger.info(f"Metric not found: {metric_name}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in search_metric for {metric_name}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in search_metric for {metric_name}: {e}")
    return None

def search_metrics_concurrently(metrics: Dict) -> Dict:
    """
    Search for all metrics concurrently, given a dictionary of metrics organized by event.
    """
    logger.info(f"Starting concurrent metric search for {len(metrics)} metrics")
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Create a list of metric names to search
        metric_names = list(metrics.keys())
        logger.info(f"Metrics to search: {metric_names}")
        
        futures = {executor.submit(search_metric, metric_name): metric_name 
                  for metric_name in metric_names 
                  if metric_name not in metric_cache}
        
        for future in as_completed(futures):
            metric_name = futures[future]
            try:
                result = future.result()
                logger.info(f"Search result for metric '{metric_name}': {result}")
                if result:
                    metric_cache[metric_name] = result
                    results[metric_name] = result
            except Exception as e:
                logger.error(f"Error processing metric '{metric_name}': {e}")

    # Add cached results
    for metric_name in metrics:
        if metric_name in metric_cache and metric_name not in results:
            results[metric_name] = metric_cache[metric_name]
            logger.info(f"Using cached result for metric '{metric_name}': {metric_cache[metric_name]}")

    return results

def search_event(event_name):
    try:
        logger.info(f"Searching for event: {event_name}")
        url = f"https://quantum.mtptest.co.uk/api/embeddings/Event/name?q={event_name.replace(' ', '+')}&compact=true&select=name&threshold=0.4"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            event = data['data'][0]  # Choose the first event if multiple are returned
            logger.info(f"Event found: {event['name']} (ID: {event['id']})")
            return event
        else:
            logger.info(f"Event not found: {event_name}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in search_event for {event_name}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in search_event for {event_name}: {e}")
    return None

def find_events_and_metrics(data, events_metrics=None):
    """
    Recursively find all events and their associated metrics in any JSON structure,
    handling deeply nested structures while maintaining event-metric relationships.
    """
    if events_metrics is None:
        events_metrics = {}
    
    def find_metrics_for_event(item, event_name):
        """
        Recursively search for metrics within an event's data structure.
        """
        if isinstance(item, dict):
            # Check if this item is a metric
            if 'metric_name' in item:
                if event_name not in events_metrics:
                    events_metrics[event_name] = []
                events_metrics[event_name].append(item)
                logger.info(f"Found metric for event '{event_name}': {item['metric_name']}")
            
            # Search all dictionary values for more metrics
            for value in item.values():
                if isinstance(value, (dict, list)):
                    find_metrics_for_event(value, event_name)
                    
        elif isinstance(item, list):
            # Search through all items in the list
            for sub_item in item:
                find_metrics_for_event(sub_item, event_name)

    def find_event_and_metrics(item):
        """
        Find events and their associated metrics at any nesting level.
        """
        if isinstance(item, dict):
            event_name = None
            
            # Check if this is an event_info structure
            if 'event_info' in item and isinstance(item['event_info'], dict):
                event_name = item['event_info'].get('event_name')
                if event_name:
                    logger.info(f"Found event: {event_name}")
                    # Look for metrics in the entire event structure
                    find_metrics_for_event(item, event_name)
            
            # Also check if this is a direct event_name entry
            elif 'event_name' in item:
                event_name = item['event_name']
                logger.info(f"Found event: {event_name}")
                # Look for metrics in the parent structure
                find_metrics_for_event(item, event_name)
            
            # Continue searching in all values
            for value in item.values():
                if isinstance(value, (dict, list)):
                    find_event_and_metrics(value)
                    
        elif isinstance(item, list):
            for sub_item in item:
                find_event_and_metrics(sub_item)
    
    # Start the search from the root
    if isinstance(data, list):
        for item in data:
            find_event_and_metrics(item)
    else:
        find_event_and_metrics(data)
    
    logger.info(f"Found events: {list(events_metrics.keys())}")
    return events_metrics

def process_event(data):
    """
    Process events and their metrics from any JSON structure.
    """
    logger.info("Starting event processing")
    
    # If data is a list, process each item separately
    if isinstance(data, list):
        logger.info("Processing list of items")
        all_results = []
        for item in data:
            results = process_event(item)
            if results:
                all_results.extend(results)
        return all_results
    
    # Find all events and their metrics in the data
    events_metrics = find_events_and_metrics(data)
    logger.info(f"Found {len(events_metrics)} events with metrics")
    
    output = []
    
    # Process each event and its metrics
    for event_name, metrics_list in events_metrics.items():
        logger.info(f"Processing event: {event_name}")
        event_info = search_event(event_name)
        
        if not event_info:
            logger.warning(f"Event not found in search: {event_name}")
            continue
            
        logger.info(f"Found event mapping: {event_name} -> {event_info['name']}")
        
        # Process metrics for this event
        for metric_data in metrics_list:
            metric_name = metric_data.get('metric_name')
            if not metric_name:
                continue
                
            logger.info(f"Searching for metric: {metric_name}")
            metric_info = search_metric(metric_name)
            
            if metric_info:
                logger.info(f"Found metric mapping: {metric_name} -> {metric_info['name']}")
                
                # Determine value type and handle string values
                value_type = metric_data.get('valueType', 'Estimated')
                min_value = metric_data.get('minValue')
                max_value = metric_data.get('maxValue', min_value)
                
                result = {
                    "taxonomy": {
                        "type": "Event",
                        "name": event_name
                    },
                    "mappedTaxonomy": {
                        "type": "Event",
                        "name": event_info['name'],
                        "id": event_info['id']
                    },
                    "metric": metric_name,
                    "mappedMetric": {
                        "name": metric_info['name'],
                        "id": metric_info['id']
                    },
                    "valueType": value_type,
                    "valueMin": min_value,
                    "valueMax": max_value,
                    "currency": metric_data.get('symbol'),
                    "magnitude": metric_data.get('magnitude')
                }
                
                output.append(result)
                logger.info(f"Added result for event '{event_name}' metric '{metric_name}'")
            else:
                logger.warning(f"No mapping found for metric: {metric_name}")
    
    logger.info(f"Completed processing all events. Generated {len(output)} results.")
    return output

@app.post("/upload/")
async def upload_pdf(file: UploadFile, background_tasks: BackgroundTasks):
    # Save uploaded file
    pdf_path = Path(temp_dir) / file.filename
    with pdf_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Start background processing and get the job_id
    job_id = await process_pdf(pdf_path)

    return {"message": "File uploaded successfully, processing started.", "job_id": job_id}

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Get the results of a completed processing job.
    """
    result_path = output_dir / f"{job_id}-final-results.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail=f"Processed results not found in {output_dir}")
    
    with open(result_path) as f:
        return JSONResponse(content=json.load(f))

@app.get("/show_extraction/{job_id}")
async def show_extraction(job_id: str):
    """
    Show the extraction process for a job.
    """
    result_path = output_dir / f"{job_id}-combined.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Processed results not found")
    
    with open(result_path) as f:
        return JSONResponse(content=json.load(f))

import markdown2
@app.get("/markdown/{job_id}")
async def get_markdown_result(job_id: str):
    """
    Get the results of a completed processing job in Markdown format.
    """
    result_path = output_dir / f"{job_id}-combined.md"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Processed results not found")
    
    with open(result_path) as f:
        markdown_content = f.read()
        html_content = markdown2.markdown(markdown_content)
        styled_html = f"""
        <html>
        <head>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/4.0.0/github-markdown.min.css">
            <style>
                body {{
                    box-sizing: border-box;
                    min-width: 200px;
                    max-width: 980px;
                    margin: 0 auto;
                    padding: 45px;
                }}
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


# curl -X POST -F "file=@C:\Users\Jawad Mansoor\ocr\data\Nielsen Sports Event Impact Assessment Presentation UNWTO April 2023 1.pdf" http://localhost:8080/upload
# curl -X POST -F "file=@C:\Users\Jawad Mansoor\ocr\data\Nielsen Sports Event Impact Assessment Presentation UNWTO April 2023 1.pdf" http://localhost:8080/upload -H "Content-Type: multipart/form-data"
# pm2 start "uvicorn plan7_test:app --workers 4 --host 0.0.0.0 --port 8080" --name quantum-data --watch
