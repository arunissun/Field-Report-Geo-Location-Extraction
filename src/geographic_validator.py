"""
Geographic Validation Module
Handles validation of city-country assignments and maintains known geographic mappings
"""

import logging
from typing import Dict, List, Any, Optional

class GeographicValidator:
    """Validates geographic location assignments and maintains known mappings"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Known geographic assignments - will be expanded based on analysis
        self.known_assignments = {
            # Russian cities
            'petropavlovsk-kamchatsky': 'russia',
            'petropavlovsk': 'russia',
            'kamchatsky': 'russia',
            'vladivostok': 'russia',
            'moscow': 'russia',
            'st.petersburg': 'russia',
            'saintpetersburg': 'russia',
            'novosibirsk': 'russia',
            'yekaterinburg': 'russia',
            'nizhniynovgorod': 'russia',
            'kazan': 'russia',
            'chelyabinsk': 'russia',
            'omsk': 'russia',
            'samara': 'russia',
            'rostovondon': 'russia',
            'ufa': 'russia',
            'krasnoyarsk': 'russia',
            'perm': 'russia',
            'voronezh': 'russia',
            'volgograd': 'russia',
            'krasnodar': 'russia',
            'saratov': 'russia',
            'tyumen': 'russia',
            'tolyatti': 'russia',
            'izhevsk': 'russia',
            
            # Australian cities
            'sydney': 'australia',
            'melbourne': 'australia',
            'brisbane': 'australia',
            'perth': 'australia',
            'adelaide': 'australia',
            'goldcoast': 'australia',
            'newcastle': 'australia',
            'canberra': 'australia',
            'sunshine coast': 'australia',
            'wollongong': 'australia',
            'hobart': 'australia',
            'geelong': 'australia',
            'townsville': 'australia',
            'cairns': 'australia',
            'darwin': 'australia',
            'toowoomba': 'australia',
            'ballarat': 'australia',
            'bendigo': 'australia',
            'albury': 'australia',
            'launeston': 'australia',
            
            # Japanese cities
            'tokyo': 'japan',
            'yokohama': 'japan',
            'osaka': 'japan',
            'nagoya': 'japan',
            'sapporo': 'japan',
            'fukuoka': 'japan',
            'kobe': 'japan',
            'kawasaki': 'japan',
            'kyoto': 'japan',
            'saitama': 'japan',
            'hiroshima': 'japan',
            'sendai': 'japan',
            'kitakyushu': 'japan',
            'chiba': 'japan',
            'sakai': 'japan',
            'niigata': 'japan',
            'hamamatsu': 'japan',
            'kumamoto': 'japan',
            'sagamihara': 'japan',
            'shizuoka': 'japan',
            'okayama': 'japan',
            'kagoshima': 'japan',
            'fukushima': 'japan',
            'kanazawa': 'japan',
            'utsunomiya': 'japan',
            'matsuyama': 'japan',
            'kurashiki': 'japan',
            'yokosuka': 'japan',
            'toyama': 'japan',
            'toyohashi': 'japan',
            'nara': 'japan',
            'gifu': 'japan',
            'fukuyama': 'japan',
            'ichikawa': 'japan',
            'iwaki': 'japan',
            'oita': 'japan',
            'naha': 'japan',
            'nagasaki': 'japan',
            'himeji': 'japan',
            'matsudo': 'japan',
            'nishinomiya': 'japan',
            'kawaguchi': 'japan',
            'kanazawa': 'japan',
            'utsunomiya': 'japan',
            'matsuyama': 'japan',
            'kurashiki': 'japan',
            'yokosuka': 'japan',
            'toyama': 'japan',
            'toyohashi': 'japan',
            'nara': 'japan',
            'gifu': 'japan',
            'fukuyama': 'japan',
            'ichikawa': 'japan',
            'iwaki': 'japan',
            'oita': 'japan',
            'naha': 'japan',
            'nagasaki': 'japan',
            'himeji': 'japan',
            'matsudo': 'japan',
            'nishinomiya': 'japan',
            'kawaguchi': 'japan',
            
            # Chinese cities
            'beijing': 'china',
            'shanghai': 'china',
            'guangzhou': 'china',
            'shenzhen': 'china',
            'tianjin': 'china',
            'wuhan': 'china',
            'dongguan': 'china',
            'chengdu': 'china',
            'nanjing': 'china',
            'chongqing': 'china',
            'xian': 'china',
            'shenyang': 'china',
            'hangzhou': 'china',
            'foshan': 'china',
            'harbin': 'china',
            'suzhou': 'china',
            'qingdao': 'china',
            'dalian': 'china',
            'zhengzhou': 'china',
            'shantou': 'china',
            'jinan': 'china',
            'changchun': 'china',
            'kunming': 'china',
            'changsha': 'china',
            'taiyuan': 'china',
            'xiamen': 'china',
            'shijiazhuang': 'china',
            'hefei': 'china',
            'urumqi': 'china',
            'fuzhou': 'china',
            'wuxi': 'china',
            'zhongshan': 'china',
            'wenzhou': 'china',
            'nanning': 'china',
            'nanchang': 'china',
            'ningbo': 'china',
            'guiyang': 'china',
            'lanzhou': 'china',
            'zhuhai': 'china',
            'haikou': 'china',
            'luoyang': 'china',
            'yinchuan': 'china',
            'baoding': 'china',
            'anshan': 'china',
            'tangshan': 'china',
            'xinyang': 'china',
            'weifang': 'china',
            'zibo': 'china',
            
            # UK cities
            'london': 'united kingdom',
            'birmingham': 'united kingdom',
            'manchester': 'united kingdom',
            'glasgow': 'united kingdom',
            'liverpool': 'united kingdom',
            'leeds': 'united kingdom',
            'sheffield': 'united kingdom',
            'edinburgh': 'united kingdom',
            'bristol': 'united kingdom',
            'cardiff': 'united kingdom',
            'belfast': 'united kingdom',
            'leicester': 'united kingdom',
            'nottingham': 'united kingdom',
            'coventry': 'united kingdom',
            'hull': 'united kingdom',
            'bradford': 'united kingdom',
            'stoke': 'united kingdom',
            'wolverhampton': 'united kingdom',
            'plymouth': 'united kingdom',
            'derby': 'united kingdom',
            'swansea': 'united kingdom',
            'southampton': 'united kingdom',
            'salford': 'united kingdom',
            'aberdeen': 'united kingdom',
            'westminster': 'united kingdom',
            'portsmouth': 'united kingdom',
            'york': 'united kingdom',
            'peterborough': 'united kingdom',
            'dundee': 'united kingdom',
            'lancaster': 'united kingdom',
            'oxford': 'united kingdom',
            'newport': 'united kingdom',
            'preston': 'united kingdom',
            'st albans': 'united kingdom',
            'norwich': 'united kingdom',
            'chester': 'united kingdom',
            'cambridge': 'united kingdom',
            'salisbury': 'united kingdom',
            'exeter': 'united kingdom',
            'gloucester': 'united kingdom',
            'lisburn': 'united kingdom',
            'chichester': 'united kingdom',
            'winchester': 'united kingdom',
            'lichfield': 'united kingdom',
            'hereford': 'united kingdom',
            'perth': 'united kingdom',
            'elgin': 'united kingdom',
            'stirling': 'united kingdom',
            'newry': 'united kingdom',
            'bangor': 'united kingdom',
            
            # French cities
            'paris': 'france',
            'marseille': 'france',
            'lyon': 'france',
            'toulouse': 'france',
            'nice': 'france',
            'nantes': 'france',
            'strasbourg': 'france',
            'montpellier': 'france',
            'bordeaux': 'france',
            'lille': 'france',
            'rennes': 'france',
            'reims': 'france',
            'lemans': 'france',
            'aix-en-provence': 'france',
            'clermont-ferrand': 'france',
            'saint-etienne': 'france',
            'tours': 'france',
            'limoges': 'france',
            'nancy': 'france',
            'grenoble': 'france',
            'angers': 'france',
            'dijon': 'france',
            'nimes': 'france',
            'saint-denis': 'france',
            'le havre': 'france',
            'toulon': 'france',
            'angers': 'france',
            'le mans': 'france',
            'brest': 'france',
            'limoges': 'france',
            'amiens': 'france',
            'tours': 'france',
            'perpignan': 'france',
            'besancon': 'france',
            'metz': 'france',
            'orleans': 'france',
            'mulhouse': 'france',
            'rouen': 'france',
            'pau': 'france',
            'nancy': 'france',
            'argenteuil': 'france',
            'montreuil': 'france',
            'caen': 'france',
            'nancy': 'france',
            
            # German cities
            'berlin': 'germany',
            'hamburg': 'germany',
            'munich': 'germany',
            'cologne': 'germany',
            'frankfurt': 'germany',
            'stuttgart': 'germany',
            'dusseldorf': 'germany',
            'dortmund': 'germany',
            'essen': 'germany',
            'leipzig': 'germany',
            'bremen': 'germany',
            'dresden': 'germany',
            'hanover': 'germany',
            'nuremberg': 'germany',
            'duisburg': 'germany',
            'bochum': 'germany',
            'wuppertal': 'germany',
            'bielefeld': 'germany',
            'bonn': 'germany',
            'munster': 'germany',
            'karlsruhe': 'germany',
            'mannheim': 'germany',
            'augsburg': 'germany',
            'wiesbaden': 'germany',
            'gelsenkirchen': 'germany',
            'monchengladbach': 'germany',
            'braunschweig': 'germany',
            'chemnitz': 'germany',
            'kiel': 'germany',
            'aachen': 'germany',
            'halle': 'germany',
            'magdeburg': 'germany',
            'freiburg': 'germany',
            'krefeld': 'germany',
            'lubeck': 'germany',
            'oberhausen': 'germany',
            'erfurt': 'germany',
            'mainz': 'germany',
            'rostock': 'germany',
            'kassel': 'germany',
            'hagen': 'germany',
            'potsdam': 'germany',
            'saarbrucken': 'germany',
            'hamm': 'germany',
            'mulheim': 'germany',
            'ludwigshafen': 'germany',
            'leverkusen': 'germany',
            'oldenburg': 'germany',
            'neuss': 'germany',
            'heidelberg': 'germany',
            
            # Italian cities
            'rome': 'italy',
            'milan': 'italy',
            'naples': 'italy',
            'turin': 'italy',
            'palermo': 'italy',
            'genoa': 'italy',
            'bologna': 'italy',
            'florence': 'italy',
            'bari': 'italy',
            'catania': 'italy',
            'venice': 'italy',
            'verona': 'italy',
            'messina': 'italy',
            'padua': 'italy',
            'trieste': 'italy',
            'taranto': 'italy',
            'brescia': 'italy',
            'prato': 'italy',
            'parma': 'italy',
            'modena': 'italy',
            'reggio calabria': 'italy',
            'reggio emilia': 'italy',
            'perugia': 'italy',
            'livorno': 'italy',
            'ravenna': 'italy',
            'cagliari': 'italy',
            'foggia': 'italy',
            'rimini': 'italy',
            'salerno': 'italy',
            'ferrara': 'italy',
            'sassari': 'italy',
            'latina': 'italy',
            'giugliano': 'italy',
            'monza': 'italy',
            'syracuse': 'italy',
            'pescara': 'italy',
            'bergamo': 'italy',
            'forlì': 'italy',
            'trento': 'italy',
            'vicenza': 'italy',
            'terni': 'italy',
            'bolzano': 'italy',
            'novara': 'italy',
            'piacenza': 'italy',
            'ancona': 'italy',
            'andria': 'italy',
            'arezzo': 'italy',
            'udine': 'italy',
            'cesena': 'italy',
            'lecce': 'italy',
            
            # Spanish cities
            'madrid': 'spain',
            'barcelona': 'spain',
            'valencia': 'spain',
            'seville': 'spain',
            'zaragoza': 'spain',
            'malaga': 'spain',
            'murcia': 'spain',
            'palma': 'spain',
            'las palmas': 'spain',
            'bilbao': 'spain',
            'alicante': 'spain',
            'cordoba': 'spain',
            'valladolid': 'spain',
            'vigo': 'spain',
            'gijon': 'spain',
            'hospitalet': 'spain',
            'vitoria': 'spain',
            'la coruna': 'spain',
            'granada': 'spain',
            'elche': 'spain',
            'oviedo': 'spain',
            'badalona': 'spain',
            'cartagena': 'spain',
            'terrassa': 'spain',
            'jerez': 'spain',
            'sabadell': 'spain',
            'santa cruz': 'spain',
            'pamplona': 'spain',
            'almeria': 'spain',
            'mostoles': 'spain',
            'fuenlabrada': 'spain',
            'leganes': 'spain',
            'donostia': 'spain',
            'burgos': 'spain',
            'albacete': 'spain',
            'santander': 'spain',
            'getafe': 'spain',
            'castellon': 'spain',
            'logrono': 'spain',
            'badajoz': 'spain',
            'huelva': 'spain',
            'leon': 'spain',
            'salamanca': 'spain',
            'tarragona': 'spain',
            'cadiz': 'spain',
            'lleida': 'spain',
            'jaen': 'spain',
            'ourense': 'spain',
            'reus': 'spain',
            'torrejon': 'spain',
            
            # Chilean locations (discovered from analysis)
            'aisen': 'chile',
            'ancud': 'chile',
            'aysen': 'chile',
            'aysén': 'chile',
            'bahiagregorio': 'chile',
            'bahiamansa': 'chile',
            'bahía gregorio': 'chile',
            'bahía mansa': 'chile',
            'boyeruca': 'chile',
            'caletameteoro': 'chile',
            'caletapaposo': 'chile',
            'caleta meteoro': 'chile',
            'caleta paposo': 'chile',
            'coliumo': 'chile',
            'easterisland': 'chile',
            'easter island': 'chile',
            'juanfernandez': 'chile',
            'juan fernandez': 'chile',
            'nehuentue': 'chile',
            'portmelinka': 'chile',
            'port melinka': 'chile',
            'puertoaguirre': 'chile',
            'puertoaldea': 'chile',
            'puertochacabuco': 'chile',
            'puertoeden': 'chile',
            'puertonatales': 'chile',
            'puertowilliams': 'chile',
            'puerto aguirre': 'chile',
            'puerto aldea': 'chile',
            'puerto chacabuco': 'chile',
            'puerto eden': 'chile',
            'puerto natales': 'chile',
            'puerto williams': 'chile',
            'puerto montt': 'chile',
            'queule': 'chile',
            'quiriquinaisland': 'chile',
            'quiriquina island': 'chile',
            'sanfelix': 'chile',
            'san félix': 'chile',
            'san felix': 'chile',
            'coronel': 'chile',
            'corralchile': 'chile',  # To distinguish from Corral elsewhere
            
            # Additional Russian locations
            'khabarovsk': 'russia',
            'magadan': 'russia',
            'petropavlovskkamchatsky': 'russia',
            'petropavlovsk-kamchatsky': 'russia',
            'yuzhnosakhalinsk': 'russia',
            'yuzhno-sakhalinsk': 'russia',
            'kamchatka': 'russia',
            
            # Costa Rican locations
            'carrillo': 'costa rica',
            'cocosisland': 'costa rica',
            'cocos island': 'costa rica',
            'esparza': 'costa rica',
            'garabito': 'costa rica',
            'golfito': 'costa rica',
            'hojancha': 'costa rica',
            'la cruz': 'costa rica',
            'lacruz': 'costa rica',
            'nandayure': 'costa rica',
            'osa': 'costa rica',
            'parrita': 'costa rica',
            'santa cruz': 'costa rica',
            'santacruz': 'costa rica',
            'puerto jiménez': 'costa rica',
            'puertojimenez': 'costa rica',
            
            # Add more as needed...
        }
        
        # Keep track of corrections made
        self.corrections_made = []
    
    def normalize_location_name(self, name: str) -> str:
        """Normalize location name for comparison"""
        if not name:
            return ""
        normalized = name.lower()
        normalized = normalized.replace(' ', '').replace('-', '').replace('.', '').replace(',', '')
        normalized = normalized.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        normalized = normalized.replace('ñ', 'n').replace('ç', 'c').replace('ü', 'u').replace('ö', 'o').replace('ä', 'a')
        return normalized
    
    def normalize_country_name(self, country: str) -> str:
        """Normalize country name for comparison"""
        if not country:
            return ""
        normalized = country.lower()
        normalized = normalized.replace(' ', '').replace('-', '').replace('.', '').replace(',', '')
        
        # Handle common country name variations
        country_variations = {
            'unitedstates': 'usa',
            'unitedstatesofamerica': 'usa',
            'us': 'usa',
            'unitedkingdom': 'united kingdom',
            'uk': 'united kingdom',
            'greatbritain': 'united kingdom',
            'britain': 'united kingdom',
            'southkorea': 'republic of korea',
            'northkorea': 'democratic peoples republic of korea',
            'drc': 'democratic republic of congo',
            'drongo': 'democratic republic of congo',
            'czechrepublic': 'czech republic',
            'uae': 'united arab emirates',
            'russia': 'russia',
            'russianfederation': 'russia',
        }
        
        return country_variations.get(normalized, normalized)
    
    def validate_city_country_assignment(self, city: str, country: str) -> bool:
        """Validate if a city belongs to the specified country"""
        city_normalized = self.normalize_location_name(city)
        country_normalized = self.normalize_country_name(country)
        
        # Check if we have a known assignment
        if city_normalized in self.known_assignments:
            expected_country = self.known_assignments[city_normalized]
            if country_normalized != expected_country:
                self.logger.warning(f"Validation failed: {city} should belong to {expected_country}, not {country}")
                return False
        
        # If not in known assignments, assume it's correct (we can't validate everything)
        return True
    
    def add_known_assignment(self, city: str, country: str):
        """Add a new known city-country assignment"""
        city_normalized = self.normalize_location_name(city)
        country_normalized = self.normalize_country_name(country)
        
        if city_normalized and country_normalized:
            self.known_assignments[city_normalized] = country_normalized
            self.logger.info(f"Added known assignment: {city} -> {country}")
    
    def analyze_unassigned_locations(self, country_associations_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze unassigned locations and suggest country assignments"""
        suggestions = {}
        
        associations = country_associations_data.get('associations', [])
        
        for association in associations:
            if not association.get('success', False):
                continue
                
            countries = association.get('countries', [])
            unassigned_states = association.get('unassigned_states', [])
            unassigned_cities = association.get('unassigned_cities', [])
            report_id = association.get('field_report_id', 'unknown')
            
            # Analyze unassigned states
            for state in unassigned_states:
                suggested_country = self._suggest_country_for_location(state, countries)
                if suggested_country:
                    key = f"{state} -> {suggested_country}"
                    if key not in suggestions:
                        suggestions[key] = []
                    suggestions[key].append(f"Report {report_id} (state)")
            
            # Analyze unassigned cities
            for city in unassigned_cities:
                suggested_country = self._suggest_country_for_location(city, countries)
                if suggested_country:
                    key = f"{city} -> {suggested_country}"
                    if key not in suggestions:
                        suggestions[key] = []
                    suggestions[key].append(f"Report {report_id} (city)")
        
        return suggestions
    
    def _suggest_country_for_location(self, location: str, available_countries: List[str]) -> Optional[str]:
        """Suggest which country a location might belong to based on available countries"""
        location_normalized = self.normalize_location_name(location)
        
        # Check if it's already in our known assignments
        if location_normalized in self.known_assignments:
            expected_country = self.known_assignments[location_normalized]
            # Check if the expected country matches any of the available countries
            for country in available_countries:
                if self.normalize_country_name(country) == expected_country:
                    return country
        
        # Simple heuristic: if location name contains country name, suggest that country
        for country in available_countries:
            country_normalized = self.normalize_country_name(country)
            if country_normalized in location_normalized or location_normalized in country_normalized:
                return country
        
        return None
    
    def get_correction_summary(self) -> Dict[str, int]:
        """Get summary of corrections made"""
        return {
            'total_corrections': len(self.corrections_made),
            'corrections_by_type': {
                'moved_to_unassigned': len([c for c in self.corrections_made if c['action'] == 'moved_to_unassigned']),
                'reassigned': len([c for c in self.corrections_made if c['action'] == 'reassigned'])
            }
        }
    
    def update_known_assignments_from_analysis(self, suggestions: Dict[str, List[str]], min_occurrences: int = 2):
        """Update known assignments based on analysis suggestions"""
        updated_count = 0
        
        for suggestion, reports in suggestions.items():
            if len(reports) >= min_occurrences:  # Only add if seen multiple times
                try:
                    location, country = suggestion.split(' -> ')
                    self.add_known_assignment(location, country)
                    updated_count += 1
                    self.logger.info(f"Added assignment based on analysis: {location} -> {country} (seen in {len(reports)} reports)")
                except ValueError:
                    continue
        
        return updated_count
