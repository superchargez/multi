import json
import logging
from pathlib import Path
from datetime import datetime
import requests
from typing import Dict, List
import asyncio
from functools import lru_cache
from rich import print

output_dir = Path("../savings/mid")
output_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(output_dir / 'processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cache for metric results
metric_cache = {}

def extract_metrics(event_data):
    """Extract metrics from event data with improved logging."""
    metrics = {}
    logger.info("Starting metric extraction")
    
    try:
        # logger.info(f"Event data structure: {json.dumps(event_data, indent=2)}")
        2+2
    except Exception as e:
        logger.warning(f"Could not log event data structure: {e}")

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

@lru_cache(maxsize=1000)
def search_metric(metric_name: str):
    """Search for a metric using its name with caching."""
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
    except Exception as e:
        logger.error(f"Error in search_metric for {metric_name}: {e}")
    return None

async def search_metrics_async(metrics: Dict) -> Dict:
    """Asynchronous version of metric searching."""
    logger.info(f"Starting async metric search for {len(metrics)} metrics")
    results = {}
    
    async def search_single_metric(metric_name):
        if metric_name in metric_cache:
            return metric_name, metric_cache[metric_name]
        try:
            result = await asyncio.to_thread(search_metric, metric_name)
            if result:
                metric_cache[metric_name] = result
            return metric_name, result
        except Exception as e:
            logger.error(f"Error searching metric '{metric_name}': {e}")
            return metric_name, None

    # Create tasks for all metrics
    tasks = [search_single_metric(metric_name) for metric_name in metrics]
    completed_searches = await asyncio.gather(*tasks)
    
    # Process results
    for metric_name, result in completed_searches:
        if result:
            results[metric_name] = result
    
    return results

@lru_cache(maxsize=1000)
def search_event(event_name: str):
    """Search for an event with caching."""
    try:
        logger.info(f"Searching for event: {event_name}")
        url = f"https://quantum.mtptest.co.uk/api/embeddings/Event/name?q={event_name.replace(' ', '+')}&compact=true&select=name&threshold=0.4"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            event = data['data'][0]
            logger.info(f"Event found: {event['name']} (ID: {event['id']})")
            return event
        else:
            logger.info(f"Event not found: {event_name}")
    except Exception as e:
        logger.error(f"Error in search_event for {event_name}: {e}")
    return None

async def process_event_async(data: Dict) -> List[Dict]:
    """Asynchronous version of event processing."""
    logger.info("Starting async event processing")
    
    if isinstance(data, list):
        all_results = []
        for item in data:
            results = await process_event_async(item)
            if results:
                all_results.extend(results)
        return all_results
    
    # Find events and metrics
    events_metrics = find_events_and_metrics(data)
    output = []
    
    # Process events concurrently
    async def process_single_event(event_name, metrics_list):
        try:
            event_info = await asyncio.to_thread(search_event, event_name)
            if not event_info:
                return []
            
            # Process metrics concurrently
            metric_results = await search_metrics_async({
                metric['metric_name']: metric 
                for metric in metrics_list 
                if 'metric_name' in metric
            })
            
            results = []
            for metric_data in metrics_list:
                metric_name = metric_data.get('metric_name')
                if not metric_name or metric_name not in metric_results:
                    continue
                
                metric_info = metric_results[metric_name]
                
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
                    "valueType": metric_data.get('valueType', 'Estimated'),
                    "valueMin": metric_data.get('minValue'),
                    "valueMax": metric_data.get('maxValue', metric_data.get('minValue')),
                    "currency": metric_data.get('symbol'),
                    "magnitude": metric_data.get('magnitude')
                }
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error processing event '{event_name}': {e}")
            return []
    
    # Create tasks for all events
    tasks = [
        process_single_event(event_name, metrics_list)
        for event_name, metrics_list in events_metrics.items()
    ]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Combine results
    for result_list in results:
        output.extend(result_list)
    
    logger.info(f"Completed async processing of all events. Generated {len(output)} results.")
    return output

def get_analysis_paths(job_id: str) -> dict[str, Path]:
    """Get all analysis-related file paths for a job ID."""
    return {
        'events': output_dir / f"{job_id}_events.json",
        'metrics': output_dir / f"{job_id}_metrics.json",
        'mappings': output_dir / f"{job_id}_mappings.json",
        'analysis': output_dir / f"{job_id}_analysis.json"
    }

async def process_analysis(job_id: str):
    """Process analysis for a job."""
    paths = get_analysis_paths(job_id)
    
    try:
        # Read the combined JSON file
        json_path = output_dir / f"{job_id}.json"
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found for job {job_id} in {output_dir}")
        
        with json_path.open('r') as f:
            data = json.load(f)
        
        # Extract metrics
        metrics = extract_metrics(data)
        await asyncio.to_thread(
            lambda: paths['metrics'].write_text(json.dumps(metrics, indent=2))
        )
        
        # Process events and generate mappings
        mappings = await process_event_async(data)
        await asyncio.to_thread(
            lambda: paths['mappings'].write_text(json.dumps(mappings, indent=2))
        )
        
        # Generate final analysis
        analysis = {
            'job_id': job_id,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics_count': len(metrics),
            'mappings_count': len(mappings),
            'metrics': metrics,
            'mappings': mappings
        }
        
        await asyncio.to_thread(
            lambda: paths['analysis'].write_text(json.dumps(analysis, indent=2))
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in process_analysis for job {job_id}: {e}")
        raise