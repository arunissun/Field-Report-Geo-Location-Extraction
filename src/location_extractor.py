
"""
ChatGPT 3.5 Turbo Location Extraction for Field Reports Pipeline
Azure OpenAI implementation for processing field reports after fetching
"""

import os
import openai
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional


class LocationExtractor:
    """Extract geographical locations from field reports using Azure OpenAI ChatGPT 3.5 Turbo"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Get Azure OpenAI credentials from environment
        self.api_key = os.environ.get("Key")
        self.endpoint = os.environ.get("Target_URL")
        self.deployment_name = os.environ.get("Deployment_Name")
        self.api_version = "2024-10-21"
        
        # Rate limiting settings
        self.rate_limit_delay = 2  # seconds between requests
        self.max_retries = 3
        
        # Validate Azure OpenAI credentials
        if not all([self.api_key, self.endpoint, self.deployment_name]):
            self.logger.warning("Azure OpenAI credentials incomplete - location extraction will be skipped")
            self.logger.warning("Required: Key, Target_URL, Deployment_Name in environment variables")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("LocationExtractor initialized successfully with Azure OpenAI")
    
    def clean_and_repair_json(self, raw_response: str) -> str:
        """Clean and attempt to repair malformed JSON responses"""
        try:
            # Remove any leading/trailing whitespace
            cleaned = raw_response.strip()
            
            # Remove any markdown code block markers if present
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            
            # Remove any text before the first { and after the last }
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned = cleaned[start_idx:end_idx + 1]
            
            # Fix common JSON issues
            # Fix unescaped quotes in strings (basic attempt)
            cleaned = re.sub(r'([^\\])"([^"]*)"([^,\]\}:])', r'\1"\2"\3', cleaned)
            
            # Fix trailing commas
            cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
            
            # Fix unterminated strings at the end (add closing quote)
            if cleaned.count('"') % 2 != 0:
                # Count quotes to see if we have an odd number
                last_quote_pos = cleaned.rfind('"')
                if last_quote_pos != -1:
                    # Check if this might be an unterminated string
                    remaining = cleaned[last_quote_pos + 1:].strip()
                    if remaining and not remaining.startswith(',') and not remaining.startswith('}') and not remaining.startswith(']'):
                        # Add closing quote before the next structural character
                        next_struct = min([pos for pos in [cleaned.find(',', last_quote_pos), 
                                         cleaned.find('}', last_quote_pos), 
                                         cleaned.find(']', last_quote_pos)] if pos > last_quote_pos] + [len(cleaned)])
                        cleaned = cleaned[:next_struct] + '"' + cleaned[next_struct:]
            
            return cleaned
            
        except Exception as e:
            self.logger.warning(f"JSON cleaning failed: {e}")
            return raw_response

    def safe_json_parse(self, raw_response: str, report_id: str) -> Dict[str, Any]:
        """Safely parse JSON with multiple fallback strategies"""
        
        # Strategy 1: Try parsing as-is
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            self.logger.debug(f"Initial JSON parse failed for report {report_id}: {e}")
        
        # Strategy 2: Clean and repair, then parse
        try:
            cleaned_response = self.clean_and_repair_json(raw_response)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            self.logger.debug(f"Cleaned JSON parse failed for report {report_id}: {e}")
        
        # Strategy 3: Try to extract JSON object manually using regex
        try:
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, raw_response, re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.debug(f"Regex JSON extraction failed for report {report_id}: {e}")
        
        # Strategy 4: Create a minimal valid response if all else fails
        self.logger.warning(f"All JSON parsing strategies failed for report {report_id}. Raw response length: {len(raw_response)}")
        self.logger.debug(f"Raw response for report {report_id}: {raw_response[:500]}..." if len(raw_response) > 500 else f"Raw response for report {report_id}: {raw_response}")
        
        # Return a basic structure that matches our expected format
        return {
            "countries": [],
            "states_regions": [],
            "cities_towns": [],
            "administrative_areas": [],
            "confidence_notes": "Failed to parse response - using fallback structure"
        }
    
    def create_system_message(self) -> str:
        """Create specialized system message for geographic location extraction"""
        return """You are an expert geographic information extraction specialist. Your task is to identify and extract geographic locations from emergency field reports with high precision.

Extract geographic locations from the title, summary, and description of field reports. Focus on:
- Countries
- States/provinces/regions  
- Cities/towns/villages
- Districts/counties/administrative areas

Return results in valid JSON format with this exact structure:
{
    "countries": ["list of countries"],
    "states_regions": ["list of states/provinces/regions"],
    "cities_towns": ["list of cities/towns/villages"], 
    "administrative_areas": ["list of districts, counties, etc."],
    "confidence_notes": "brief note about extraction confidence"
}

CRITICAL JSON FORMATTING RULES:
- Return ONLY valid JSON, no additional text or explanations
- Use double quotes for all strings
- Ensure all strings are properly closed with quotes
- No trailing commas
- No line breaks within string values
- Escape any quotes within string values using \"
- Keep location names concise and avoid very long descriptions

Rules:
- Extract ONLY political/administrative geographic entities
- Remove duplicates within the same field report
- Include locations even if mentioned only once
- Focus on emergency/disaster context locations
- Be thorough but accurate
- Return ONLY the JSON, no additional text"""

    def combine_report_text(self, report: Dict[str, Any]) -> str:
        """Combine title, summary, and description into a single text for analysis"""
        text_parts = []
        
        # Add title
        title = report.get('title', '').strip()
        if title:
            text_parts.append(f"TITLE: {title}")
        
        # Add summary  
        summary = report.get('summary', '').strip()
        if summary:
            text_parts.append(f"SUMMARY: {summary}")
            
        # Add description
        description = report.get('description', '').strip()
        if description:
            text_parts.append(f"DESCRIPTION: {description}")
        
        combined_text = "\n\n".join(text_parts)
        
        # Limit text length to prevent token limit issues and response truncation
        max_chars = 4000  # Reasonable limit to prevent overly long responses
        if len(combined_text) > max_chars:
            combined_text = combined_text[:max_chars] + "... [TEXT TRUNCATED]"
            
        return combined_text

    async def extract_geonames_from_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Extract geonames from a single field report using Azure OpenAI"""
        
        if not self.enabled:
            return {
                "id": report.get('id', 'unknown'),
                "success": False,
                "error": "Azure OpenAI credentials not configured properly",
                "countries": [],
                "states_regions": [],
                "cities_towns": [],
                "administrative_areas": [],
                "confidence_notes": "API not configured",
                "total_locations_found": 0,
                "extracted_at": datetime.now().isoformat()
            }
        
        report_id = report.get('id', 'unknown')
        
        # Combine text from all available fields
        combined_text = self.combine_report_text(report)
        
        if not combined_text.strip():
            return {
                "id": report_id,
                "success": False,
                "error": "No text content found in report",
                "countries": [],
                "states_regions": [],
                "cities_towns": [],
                "administrative_areas": [],
                "confidence_notes": "No content to analyze",
                "total_locations_found": 0,
                "extracted_at": datetime.now().isoformat()
            }
        
        # Create the extraction prompt
        extraction_prompt = f"""Extract all geographic locations from the following field report:
        FIELD REPORT ID: {report_id} {combined_text} 
        Return only valid JSON with the extracted geonames categorized as specified."""
        
        # Create message structure
        messages = [
            {"role": "system", "content": self.create_system_message()},
            {"role": "user", "content": extraction_prompt}
        ]
        
        # Call Azure OpenAI API with retry logic
        for attempt in range(self.max_retries):
            try:
                async with openai.AsyncAzureOpenAI(
                    api_key=self.api_key,
                    azure_endpoint=self.endpoint,
                    api_version=self.api_version
                ) as client:
                    self.logger.debug(f"Calling Azure OpenAI API for report {report_id}, attempt {attempt + 1}")
                    
                    response = await client.chat.completions.create(
                        model=self.deployment_name,  # This is the deployment name for Azure
                        messages=messages,
                        temperature=0.0,  # Use 0 for most consistent JSON generation
                        max_tokens=1500,  # Increased token limit
                        response_format={"type": "json_object"}
                    )
                    
                    # Parse the response using safe parsing
                    raw_response = response.choices[0].message.content.strip()
                    
                    # Use safe JSON parsing with multiple fallback strategies
                    extracted_data = self.safe_json_parse(raw_response, report_id)
                    
                    # Ensure all expected keys exist
                    expected_keys = ["countries", "states_regions", "cities_towns", "administrative_areas"]
                    for key in expected_keys:
                        if key not in extracted_data:
                            extracted_data[key] = []
                    
                    # Remove duplicates within each category
                    for key in expected_keys:
                        if isinstance(extracted_data[key], list):
                            extracted_data[key] = list(set(extracted_data[key]))  # Remove duplicates
                            extracted_data[key].sort()  # Sort for consistency
                    
                    # Add metadata
                    result = {
                        "id": report_id,
                        "success": True,
                        "extracted_at": datetime.now().isoformat(),
                        "total_locations_found": sum(len(locations) for locations in extracted_data.values() if isinstance(locations, list)),
                        **extracted_data  # Unpack the extracted location data
                    }
                    
                    self.logger.debug(f"Successfully extracted {result['total_locations_found']} locations from report {report_id}")
                    return result
                        
            except Exception as e:
                self.logger.error(f"Azure OpenAI API call failed for report {report_id}, attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:  # Last attempt
                    return {
                        "id": report_id,
                        "success": False,
                        "error": f"Error calling Azure OpenAI API: {str(e)}",
                        "countries": [],
                        "states_regions": [],
                        "cities_towns": [],
                        "administrative_areas": [],
                        "confidence_notes": "API call failed",
                        "total_locations_found": 0,
                        "extracted_at": datetime.now().isoformat()
                    }
            
            # Wait before retry
            await asyncio.sleep(self.rate_limit_delay)
        
        # This should never be reached, but just in case
        return {
            "id": report_id,
            "success": False,
            "error": "Unexpected error in extraction process",
            "countries": [],
            "states_regions": [],
            "cities_towns": [],
            "administrative_areas": [],
            "confidence_notes": "Unexpected error",
            "total_locations_found": 0,
            "extracted_at": datetime.now().isoformat()
        }

    async def process_reports_batch(self, reports: List[Dict[str, Any]], batch_size: int = 3) -> List[Dict[str, Any]]:
        """Process multiple field reports in batches to respect rate limits"""
        
        if not self.enabled:
            self.logger.info("Location extraction skipped - Azure OpenAI credentials not configured properly")
            return []
        
        if not reports:
            return []
        
        all_results = []
        total_reports = len(reports)
        
        self.logger.info(f"[LOCATION] Starting location extraction for {total_reports} field reports using Azure OpenAI...")
        
        for i in range(0, total_reports, batch_size):
            batch = reports[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_reports + batch_size - 1) // batch_size
            
            self.logger.info(f"Processing location extraction batch {batch_num}/{total_batches} ({len(batch)} reports)")
            
            # Create tasks for concurrent processing within the batch
            tasks = []
            for report in batch:
                tasks.append(self.extract_geonames_from_report(report))
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    report_id = batch[j].get('id', 'unknown')
                    self.logger.error(f"Exception processing report {report_id}: {result}")
                    error_result = {
                        "id": report_id,
                        "success": False,
                        "error": f"Processing exception: {str(result)}",
                        "countries": [],
                        "states_regions": [],
                        "cities_towns": [],
                        "administrative_areas": [],
                        "confidence_notes": "Processing exception",
                        "total_locations_found": 0,
                        "extracted_at": datetime.now().isoformat()
                    }
                    all_results.append(error_result)
                else:
                    all_results.append(result)
            
            # Rate limiting between batches
            if i + batch_size < total_reports:
                self.logger.info("Waiting 5 seconds between batches for rate limiting...")
                await asyncio.sleep(5)  # Wait 5 seconds between batches
        
        successful_extractions = sum(1 for result in all_results if result.get('success', False))
        total_locations = sum(result.get('total_locations_found', 0) for result in all_results)
        
        self.logger.info(f"[LOCATION] Location extraction completed: {successful_extractions}/{total_reports} successful, {total_locations} total locations found")
        
        return all_results
