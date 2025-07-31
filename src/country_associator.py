
"""
Country-Location Associator using Azure OpenAI ChatGPT 3.5 Turbo
Associates extracted locations with their correct countries - Simplified Structure
"""

import os
import openai
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from geographic_validator import GeographicValidator

class CountryAssociator:
    """Associate extracted locations with their correct countries using Azure OpenAI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize geographic validator
        self.validator = GeographicValidator()
        
        # Get Azure OpenAI credentials from environment
        self.api_key = os.environ.get("Key")
        self.endpoint = os.environ.get("Target_URL")
        self.deployment_name = os.environ.get("Deployment_Name")
        self.api_version = "2024-10-21"
        
        # Rate limiting settings
        self.rate_limit_delay = 2
        self.max_retries = 3
        
        # Validate credentials
        if not all([self.api_key, self.endpoint, self.deployment_name]):
            self.logger.warning("Azure OpenAI credentials incomplete - country association will be skipped")
            self.logger.warning("Required environment variables: Key, Target_URL, Deployment_Name")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("CountryAssociator initialized successfully with Azure OpenAI")
    
    def normalize_country_name(self, country: str) -> str:
        """Convert country name to field-safe format"""
        return self.validator.normalize_country_name(country).replace(' ', '_')
    
    def validate_city_country_assignment(self, city: str, country: str) -> bool:
        """Validate city-country assignment using the geographic validator"""
        return self.validator.validate_city_country_assignment(city, country)
    
    def correct_obvious_errors(self, association_data: Dict[str, Any]) -> Dict[str, Any]:
        """Correct obvious geographic assignment errors using the validator"""
        corrected_data = association_data.copy()
        
        # Get all countries from the data
        countries = corrected_data.get('countries', [])
        
        # Check each country's cities for errors
        for country in countries:
            normalized_country = self.normalize_country_name(country)
            cities_key = f"{normalized_country}_cities"
            
            if cities_key in corrected_data:
                cities = corrected_data[cities_key].copy()
                corrected_cities = []
                moved_to_unassigned = []
                
                for city in cities:
                    if self.validate_city_country_assignment(city, country):
                        corrected_cities.append(city)
                    else:
                        moved_to_unassigned.append(city)
                        self.logger.info(f"Moving {city} to unassigned (was incorrectly assigned to {country})")
                
                # Update the cities list
                corrected_data[cities_key] = corrected_cities
                
                # Add to unassigned cities
                if moved_to_unassigned:
                    unassigned_cities = corrected_data.get('unassigned_cities', [])
                    unassigned_cities.extend(moved_to_unassigned)
                    corrected_data['unassigned_cities'] = unassigned_cities
        
        return corrected_data
    
    def reassign_unassigned_locations(self, association_data: Dict[str, Any]) -> Dict[str, Any]:
        """Try to reassign unassigned locations using the validator's knowledge"""
        updated_data = association_data.copy()
        
        countries = updated_data.get('countries', [])
        unassigned_states = updated_data.get('unassigned_states', [])
        unassigned_cities = updated_data.get('unassigned_cities', [])
        
        # Try to reassign unassigned states
        remaining_states = []
        for state in unassigned_states:
            reassigned = False
            for country in countries:
                if self.validator.validate_city_country_assignment(state, country):
                    # Check if validator knows this location belongs to this country
                    state_normalized = self.validator.normalize_location_name(state)
                    country_normalized = self.validator.normalize_country_name(country)
                    
                    if state_normalized in self.validator.known_assignments:
                        expected_country = self.validator.known_assignments[state_normalized]
                        if expected_country == country_normalized:
                            # Reassign to this country
                            normalized_country = self.normalize_country_name(country)
                            states_key = f"{normalized_country}_states"
                            
                            if states_key not in updated_data:
                                updated_data[states_key] = []
                            updated_data[states_key].append(state)
                            
                            self.logger.info(f"Reassigned {state} to {country} based on validator knowledge")
                            reassigned = True
                            break
            
            if not reassigned:
                remaining_states.append(state)
        
        # Try to reassign unassigned cities
        remaining_cities = []
        for city in unassigned_cities:
            reassigned = False
            for country in countries:
                # Check if validator knows this location belongs to this country
                city_normalized = self.validator.normalize_location_name(city)
                country_normalized = self.validator.normalize_country_name(country)
                
                if city_normalized in self.validator.known_assignments:
                    expected_country = self.validator.known_assignments[city_normalized]
                    if expected_country == country_normalized:
                        # Reassign to this country
                        normalized_country = self.normalize_country_name(country)
                        cities_key = f"{normalized_country}_cities"
                        
                        if cities_key not in updated_data:
                            updated_data[cities_key] = []
                        updated_data[cities_key].append(city)
                        
                        self.logger.info(f"Reassigned {city} to {country} based on validator knowledge")
                        reassigned = True
                        break
            
            if not reassigned:
                remaining_cities.append(city)
        
        # Update the unassigned lists
        updated_data['unassigned_states'] = remaining_states
        updated_data['unassigned_cities'] = remaining_cities
        
        return updated_data
    
    def create_simplified_association_prompt(self, countries: List[str], states_regions: List[str], 
                                           cities_towns: List[str], report_id: str) -> str:
        """Create prompt for simplified country-location association"""
        
        # Create dynamic field names based on countries
        json_structure = {
            "field_report_id": report_id,
            "countries": countries,
            "confidence_notes": "explanation of assignment logic"
        }
        
        # Add country-specific fields
        for country in countries:
            normalized = self.normalize_country_name(country)
            json_structure[f"{normalized}_states"] = ["list of states/regions for this country"]
            json_structure[f"{normalized}_cities"] = ["list of cities/towns for this country"]
        
        # Add unassigned fields
        json_structure["unassigned_states"] = ["states that don't belong to any mentioned country"]
        json_structure["unassigned_cities"] = ["cities that don't belong to any mentioned country"]
        
        countries_str = ", ".join(countries) if countries else "No countries specified"
        states_str = ", ".join(states_regions) if states_regions else "No states/regions"
        cities_str = ", ".join(cities_towns) if cities_towns else "No cities/towns"
        
        return f"""You are a geographic expert with extensive knowledge of world geography. Assign each location to its correct country using precise geographic knowledge.

CRITICAL INSTRUCTIONS:
- ONLY assign locations to countries you are 100% certain about
- If you are unsure about any location, put it in unassigned_states or unassigned_cities
- Use your knowledge of actual administrative divisions and geographic boundaries
- Be extremely careful with similar-sounding place names from different countries
- Cities like Petropavlovsk-Kamchatsky belong to Russia (Kamchatka Peninsula)
- Double-check each assignment against your geographic knowledge

FIELD REPORT ID: {report_id}
COUNTRIES: {countries_str}
STATES/REGIONS TO ASSIGN: {states_str}
CITIES/TOWNS TO ASSIGN: {cities_str}

Return EXACTLY this JSON structure:
{json.dumps(json_structure, indent=2)}

ASSIGNMENT RULES:
1. Only assign locations to countries where you have high confidence
2. When in doubt, use unassigned_states or unassigned_cities
3. Consider geographic proximity and administrative boundaries
4. Verify each assignment against known geographic facts
5. Be conservative - it's better to leave something unassigned than assign it incorrectly

Return ONLY the JSON, no additional text."""

    async def associate_locations_for_report(self, extraction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Associate locations with countries for a single field report - simplified output"""
        
        if not self.enabled:
            return {
                "field_report_id": extraction_data.get('id', 'unknown'),
                "success": False,
                "error": "Azure OpenAI credentials not configured",
                "processed_at": datetime.now().isoformat()
            }
        
        report_id = extraction_data.get('id', 'unknown')
        countries = extraction_data.get('countries', [])
        states_regions = extraction_data.get('states_regions', [])
        cities_towns = extraction_data.get('cities_towns', [])
        
        self.logger.debug(f"Processing association for report {report_id}: {len(countries)} countries, {len(states_regions)} states, {len(cities_towns)} cities")
        
        # CRITICAL CHECK: If no countries identified, do NOT proceed further
        if not countries:
            self.logger.info(f"Report {report_id}: No countries identified - skipping country association")
            return {
                "field_report_id": report_id,
                "success": False,
                "error": "No countries identified - country association skipped",
                "unassigned_states": states_regions,
                "unassigned_cities": cities_towns,
                "confidence_notes": "No countries identified - cannot proceed with association",
                "processed_at": datetime.now().isoformat()
            }
        
        # Skip if no locations to process
        if not states_regions and not cities_towns:
            self.logger.debug(f"Report {report_id}: No states/regions or cities/towns to associate")
            return {
                "field_report_id": report_id,
                "success": False,
                "error": "No states/regions or cities/towns to associate",
                "processed_at": datetime.now().isoformat()
            }
        
        # If only one country, assign all locations to it automatically
        if len(countries) == 1:
            country = countries[0]
            normalized = self.normalize_country_name(country)
            
            result = {
                "field_report_id": report_id,
                "success": True,
                "countries": countries,
                f"{normalized}_states": states_regions,
                f"{normalized}_cities": cities_towns,
                "unassigned_states": [],
                "unassigned_cities": [],
                "confidence_notes": f"Single country ({country}) - all locations assigned automatically",
                "processed_at": datetime.now().isoformat()
            }
            
            # Apply validation even for single country assignments
            result = self.correct_obvious_errors(result)
            result = self.reassign_unassigned_locations(result)
            
            self.logger.debug(f"Single country assignment for report {report_id}: {country}")
            return result
        
        # Multi-country scenario - use ChatGPT for intelligent assignment
        self.logger.debug(f"Multi-country scenario for report {report_id}: {countries}")
        prompt = self.create_simplified_association_prompt(countries, states_regions, cities_towns, report_id)
        
        messages = [
            {"role": "system", "content": "You are a geographic expert with comprehensive knowledge of world administrative divisions, cities, and regional geography. Always return valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        # Call Azure OpenAI API with retry logic
        for attempt in range(self.max_retries):
            try:
                async with openai.AsyncAzureOpenAI(
                    api_key=self.api_key,
                    azure_endpoint=self.endpoint,
                    api_version=self.api_version
                ) as client:
                    
                    self.logger.debug(f"Calling Azure OpenAI for country association - Report {report_id}, attempt {attempt + 1}")
                    
                    response = await client.chat.completions.create(
                        model=self.deployment_name,
                        messages=messages,
                        temperature=0.0,  # Use 0.0 for most deterministic results
                        max_tokens=1500,
                        response_format={"type": "json_object"}
                    )
                    
                    raw_response = response.choices[0].message.content.strip()
                    
                    try:
                        association_data = json.loads(raw_response)
                        
                        # Apply validation and corrections
                        association_data = self.correct_obvious_errors(association_data)
                        association_data = self.reassign_unassigned_locations(association_data)
                        
                        # Enhance the response with metadata
                        association_data["success"] = True
                        association_data["processed_at"] = datetime.now().isoformat()
                        
                        self.logger.info(f"Successfully associated locations for report {report_id}")
                        return association_data
                        
                    except json.JSONDecodeError as json_error:
                        self.logger.error(f"JSON parsing failed for report {report_id}: {json_error}")
                        if attempt == self.max_retries - 1:
                            error_result = {
                                "field_report_id": report_id,
                                "success": False,
                                "error": f"Failed to parse association response: {str(json_error)}",
                                "unassigned_states": states_regions,
                                "unassigned_cities": cities_towns,
                                "processed_at": datetime.now().isoformat()
                            }
                            return error_result
                
            except Exception as e:
                self.logger.error(f"Azure OpenAI API call failed for report {report_id}, attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    error_result = {
                        "field_report_id": report_id,
                        "success": False,
                        "error": f"API call failed: {str(e)}",
                        "unassigned_states": states_regions,
                        "unassigned_cities": cities_towns,
                        "processed_at": datetime.now().isoformat()
                    }
                    return error_result
            
            await asyncio.sleep(self.rate_limit_delay)
        
        # Fallback response with simplified structure
        return {
            "field_report_id": report_id,
            "success": False,
            "error": "Unexpected error in association process",
            "unassigned_states": states_regions,
            "unassigned_cities": cities_towns,
            "processed_at": datetime.now().isoformat()
        }
