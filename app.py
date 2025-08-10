import streamlit as st
import google.generativeai as genai
import base64
import io
from PIL import Image
import json
from typing import Dict, Any, List
import os
import requests
from azure.storage.blob import BlobServiceClient, BlobClient
import uuid
from datetime import datetime, timedelta
import tempfile
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the page
st.set_page_config(
    page_title="GeoGuess AI - See exactly where that picture was taken 🕵️‍♂️",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-bg: #0a0f1a;
        --secondary-bg: #0e1520;
        --accent-bg: #1a2332;
        --card-bg: rgba(26, 35, 50, 0.9);
        --glass-bg: rgba(173, 216, 230, 0.08);
        --border-color: rgba(173, 216, 230, 0.15);
        --text-primary: #e8f4f8;
        --text-secondary: rgba(232, 244, 248, 0.8);
        --text-muted: rgba(232, 244, 248, 0.9);
        --accent-red: #B3124A;
        --accent-green: #C5D473;
        --accent-purple: #8B4513;
        --accent-blue: #87CEEB;
        --success-color: #C5D473;
        --warning-color: #8B4513;
        --error-color: #B3124A;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 50%, #1e2a3a 100%);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    .main-header {
        text-align: center;
        background: linear-gradient(45deg, var(--accent-red), var(--accent-blue), var(--accent-green));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(135, 206, 235, 0.4);
    }
    
    .slogan {
        text-align: center;
        color: var(--text-secondary);
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    .subtitle {
        text-align: center;
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-bottom: 3rem;
        padding: 0 2rem;
        line-height: 1.6;
    }
    
    .result-container {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        padding: 2rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        color: var(--text-primary);
    }
    
    .confidence-high {
        color: var(--success-color);
        font-weight: 600;
        text-shadow: 0 0 8px rgba(197, 212, 115, 0.5);
    }
    .confidence-medium {
        color: var(--warning-color);
        font-weight: 600;
        text-shadow: 0 0 8px rgba(139, 69, 19, 0.5);
    }
    .confidence-low {
        color: var(--error-color);
        font-weight: 600;
        text-shadow: 0 0 8px rgba(179, 18, 74, 0.5);
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, var(--accent-red), var(--accent-blue), var(--accent-green)) !important;
        color: var(--text-primary) !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 1rem 2rem !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(135, 206, 235, 0.4) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(135, 206, 235, 0.6) !important;
    }
    
    .method-tab {
        padding: 2rem;
        border-radius: 16px;
        margin: 1rem 0;
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        color: var(--text-primary);
    }
    
    .method-tab:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
    }
    
    .gemini-tab {
        background: linear-gradient(135deg, rgba(135, 206, 235, 0.15), rgba(197, 212, 115, 0.1));
        border-left: 4px solid var(--accent-blue);
    }
    
    .googlelens-tab {
        background: linear-gradient(135deg, rgba(179, 18, 74, 0.15), rgba(135, 206, 235, 0.1));
        border-left: 4px solid var(--accent-red);
    }
    
    .debug-section {
        background: var(--accent-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(8px);
        color: var(--text-primary);
    }
    
    .url-box {
        background: var(--primary-bg);
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Fira Code', monospace;
        word-break: break-all;
        color: var(--accent-green);
        border: 1px solid rgba(197, 212, 115, 0.3);
        font-size: 0.9rem;
    }
    
    .location-match {
        background: linear-gradient(135deg, rgba(197, 212, 115, 0.15), rgba(139, 69, 19, 0.1));
        border: 1px solid rgba(197, 212, 115, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(8px);
        color: var(--text-primary);
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc {
        background: rgba(26, 35, 50, 0.95) !important;
        backdrop-filter: blur(20px) !important;
    }
    
    /* Sidebar text */
    .css-1d391kg .stMarkdown, .css-1lcbmhc .stMarkdown {
        color: var(--text-primary) !important;
    }
    
    /* Select box styling */
    .stSelectbox > div > div {
        background-color: var(--accent-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox > div > div > div {
        color: var(--text-primary) !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent-red), var(--accent-blue), var(--accent-green)) !important;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        background: var(--accent-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--text-muted) !important;
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        border-radius: 16px !important;
        border: 2px dashed rgba(139, 69, 19, 0.4) !important;
        background: var(--glass-bg) !important;
        padding: 2rem !important;
    }
    
    .upload-area {
        border: 2px dashed var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
        color: var(--text-secondary);
    }
    
    .upload-area:hover {
        border-color: var(--accent-purple);
        background: rgba(139, 69, 19, 0.05);
        color: var(--text-primary);
    }
    
    .emoji-large {
        font-size: 3rem;
        margin: 1rem 0;
        opacity: 0.8;
    }
    
    .feature-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
        color: var(--text-primary);
    }
    
    .feature-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
        border-color: var(--accent-purple);
    }
    
    .success-message {
        background: linear-gradient(135deg, rgba(197, 212, 115, 0.15), rgba(139, 69, 19, 0.1));
        border: 1px solid rgba(197, 212, 115, 0.3);
        border-radius: 12px;
        padding: 1rem;
        color: var(--success-color);
        font-weight: 500;
    }
    
    .warning-message {
        background: linear-gradient(135deg, rgba(139, 69, 19, 0.15), rgba(179, 18, 74, 0.1));
        border: 1px solid rgba(139, 69, 19, 0.3);
        border-radius: 12px;
        padding: 1rem;
        color: var(--warning-color);
        font-weight: 500;
    }
    
    .joe-quote {
        font-style: italic;
        color: var(--text-muted);
        text-align: center;
        margin: 2rem 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    .neon-text {
        text-shadow: 0 0 8px rgba(139, 69, 19, 0.6);
        color: var(--accent-purple);
        font-weight: 600;
    }
    
    /* Additional text elements */
    .stMarkdown p, .stMarkdown div {
        color: var(--text-primary);
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--text-primary);
    }
    
    /* Metric styling */
    .css-1wivap2, .css-1wivap2 > div {
        color: var(--text-primary) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--accent-bg) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expanderContent {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--accent-bg) !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent-blue) !important;
        color: var(--text-primary) !important;
    }
    
    /* Radio button styling */
    .stRadio > div {
        color: var(--text-primary) !important;
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        color: var(--text-primary) !important;
    }
    
    /* Change pink checkboxes and radio buttons to brown */
    .stCheckbox svg, .stRadio svg {
        fill: #8B4513 !important;
    }
    
    /* Sidebar checkbox and radio button colors */
    .css-1d391kg .stCheckbox svg, 
    .css-1lcbmhc .stCheckbox svg,
    .css-1d391kg .stRadio svg,
    .css-1lcbmhc .stRadio svg {
        fill: #8B4513 !important;
    }
            
    section[data-testid="stSidebar"] {
    background-color: #8B4513 !important;
    color: white !important;
}
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
</style>

    
""", unsafe_allow_html=True)

class AzureBlobManager:
    def __init__(self, connection_string: str, container_name: str = "universal-geoguesser-images"):
        """Initialize Azure Blob Storage client."""
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = container_name
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.get_container_properties()
        except Exception:
            # Container doesn't exist, create it
            container_client = self.blob_service_client.create_container(
                self.container_name,
                public_access='blob'  # Allow public read access to blobs
            )
    
    def upload_image(self, image: Image.Image, filename: str = None) -> str:
        """
        Upload image to Azure Blob Storage and return public URL.
        
        Args:
            image: PIL Image object
            filename: Optional custom filename
            
        Returns:
            Public URL of the uploaded image
        """
        # Generate unique filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"location_{timestamp}_{unique_id}.jpg"
        
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        # Convert to RGB if image has transparency
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        # Upload to Azure Blob Storage
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, 
            blob=filename
        )
        
        blob_client.upload_blob(
            img_byte_arr.getvalue(), 
            overwrite=True,
            content_type='image/jpeg'
        )
        
        # Return public URL
        return blob_client.url
    
    def delete_image(self, filename: str):
        """Delete image from Azure Blob Storage."""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=filename
            )
            blob_client.delete_blob()
        except Exception as e:
            st.warning(f"Could not delete image: {str(e)}")

class GoogleLensAnalyzer:
    def __init__(self, serpapi_key: str, gemini_model=None):
        """Initialize Google Lens analyzer with SerpAPI and optional Gemini model."""
        self.serpapi_key = serpapi_key
        self.base_url = "https://serpapi.com/search"
        self.gemini_model = gemini_model
    
    def extract_location_info_from_serpapi(self, data: Dict) -> Dict[str, Any]:
        """
        Enhanced extraction of location information from SerpAPI JSON response.
        
        Args:
            data: SerpAPI JSON response
            
        Returns:
            Dict containing extracted location information
        """
        location_info = {
            'primary_locations': [],
            'businesses': [],
            'landmarks': [],
            'geographical_features': [],
            'addresses': [],
            'titles': [],
            'sources': []
        }
        
        # Extract from Knowledge Graph (highest priority)
        knowledge_graph = data.get('knowledge_graph', {})
        if knowledge_graph:
            kg_title = knowledge_graph.get('title', '')
            kg_description = knowledge_graph.get('description', '')
            kg_type = knowledge_graph.get('type', '')
            
            if kg_title:
                location_info['primary_locations'].append({
                    'name': kg_title,
                    'description': kg_description,
                    'type': kg_type,
                    'confidence': 0.9,
                    'source': 'knowledge_graph'
                })
        
        # Extract from Visual Matches
        visual_matches = data.get('visual_matches', [])
        for match in visual_matches:
            title = match.get('title', '')
            source = match.get('source', '')
            link = match.get('link', '')
            
            if title:
                location_info['titles'].append(title)
                location_info['sources'].append({
                    'title': title,
                    'source': source,
                    'link': link
                })
                
                # Extract potential business names and locations
                self._extract_business_info(title, location_info)
        
        # Extract from Reverse Image Search results
        reverse_image_search = data.get('reverse_image_search', {})
        if reverse_image_search:
            for result in reverse_image_search.get('results', []):
                title = result.get('title', '')
                if title:
                    location_info['titles'].append(title)
                    self._extract_business_info(title, location_info)
        
        return location_info
    
    def _extract_business_info(self, text: str, location_info: Dict):
        """
        Extract business and location information from text using patterns.
        
        Args:
            text: Text to analyze
            location_info: Dictionary to update with found information
        """
        text_lower = text.lower()
        
        # Business type keywords (universal)
        business_keywords = [
            'restaurant', 'cafe', 'coffee', 'hotel', 'resort', 'mall', 'plaza', 
            'shopping', 'store', 'bar', 'pub', 'club', 'theater', 'cinema',
            'museum', 'gallery', 'park', 'beach', 'station', 'airport',
            'hospital', 'school', 'university', 'library', 'bank', 'market'
        ]
        
        # Check for business types
        for keyword in business_keywords:
            if keyword in text_lower:
                location_info['businesses'].append({
                    'text': text,
                    'type': keyword,
                    'confidence': 0.6
                })
                break
        
        # Extract potential addresses using regex patterns
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
            r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2,}',  # City, State/Country pattern
            r'\d{5}(?:-\d{4})?'  # Postal codes
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                location_info['addresses'].append(match.strip())
        
        # Extract landmark indicators
        landmark_keywords = [
            'tower', 'bridge', 'monument', 'statue', 'cathedral', 'church',
            'temple', 'mosque', 'palace', 'castle', 'fort', 'plaza', 'square'
        ]
        
        for keyword in landmark_keywords:
            if keyword in text_lower:
                location_info['landmarks'].append({
                    'text': text,
                    'type': keyword,
                    'confidence': 0.7
                })
                break
    
    def analyze_with_ai(self, location_info: Dict) -> Dict[str, Any]:
        """
        Use Gemini AI to analyze extracted location information.
        
        Args:
            location_info: Dictionary containing extracted location information
            
        Returns:
            Dict containing AI analysis
        """
        if not self.gemini_model:
            return {
                "locationGuess": "No AI model available",
                "confidence": 0.0,
                "reasoning": "AI analysis not available"
            }
        
        # Prepare comprehensive data for AI analysis
        analysis_data = {
            'titles': location_info.get('titles', [])[:15],  # Top 15 titles
            'primary_locations': location_info.get('primary_locations', []),
            'businesses': location_info.get('businesses', []),
            'landmarks': location_info.get('landmarks', []),
            'addresses': location_info.get('addresses', [])
        }
        
        # Create detailed prompt
        prompt = f"""You are a world-class location analyst with expertise in identifying places from various types of textual evidence. Analyze the following information extracted from reverse image search results to determine the most likely specific location.

EXTRACTED INFORMATION:
===================

Primary Locations (from Knowledge Graph):
{json.dumps(analysis_data['primary_locations'], indent=2)}

Titles from Similar Images:
{chr(10).join([f"- {title}" for title in analysis_data['titles']])}

Identified Businesses:
{json.dumps(analysis_data['businesses'], indent=2)}

Identified Landmarks:
{json.dumps(analysis_data['landmarks'], indent=2)}

Found Addresses:
{analysis_data['addresses']}

ANALYSIS REQUIREMENTS:
====================
1. Look for the most specific location possible (exact business name, landmark, or address)
2. Consider geographical context clues from all sources
3. Prioritize information from Knowledge Graph if available
4. Cross-reference information between different sources
5. Be globally aware - don't assume any specific region unless clearly indicated

Provide your analysis in JSON format:
{{
    "locationGuess": "Most specific location name you can determine (e.g., 'Times Square, New York', 'Eiffel Tower, Paris', 'Specific Restaurant Name, City')",
    "confidence": 0.8,
    "reasoning": "Detailed explanation of your analysis process and why you arrived at this conclusion",
    "primaryEvidence": "The key piece of evidence that led to your conclusion",
    "alternativeLocations": ["Other possible locations if confidence is not high"]
}}

Confidence scale: 1.0 = Absolutely certain, 0.8+ = Very confident, 0.6+ = Moderately confident, 0.4+ = Low confidence, <0.4 = Very uncertain"""

        try:
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                return {
                    "locationGuess": "Could not parse AI response",
                    "confidence": 0.0,
                    "reasoning": "Failed to parse AI analysis",
                    "primaryEvidence": "None",
                    "alternativeLocations": []
                }
                
        except Exception as e:
            return {
                "locationGuess": f"AI analysis failed: {str(e)}",
                "confidence": 0.0,
                "reasoning": f"Error in AI analysis: {str(e)}",
                "primaryEvidence": "Error occurred",
                "alternativeLocations": []
            }
    
    def analyze_image_url(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze image using Google Lens via SerpAPI with enhanced data extraction.
        
        Args:
            image_url: Public URL of the image
            
        Returns:
            Dict containing analysis results
        """
        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": self.serpapi_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Enhanced data extraction
            location_info = self.extract_location_info_from_serpapi(data)
            
            # AI analysis of extracted information
            ai_analysis = self.analyze_with_ai(location_info)
            
            # Determine best location guess from available data
            location_guess = "Location could not be determined"
            confidence = 0.1
            caption = "Image analyzed with Google Lens"
            
            # Prioritize Knowledge Graph results
            if location_info['primary_locations']:
                primary = location_info['primary_locations'][0]
                location_guess = primary['name']
                confidence = primary['confidence']
                caption = f"Identified from knowledge graph: {primary.get('description', 'No description')}"
            
            # Use AI analysis if it has higher confidence
            if ai_analysis.get('confidence', 0) > confidence:
                location_guess = ai_analysis.get('locationGuess', location_guess)
                confidence = ai_analysis.get('confidence', confidence)
                caption = f"AI analysis: {ai_analysis.get('reasoning', 'Based on comprehensive analysis')}"
            
            return {
                "locationGuess": location_guess,
                "caption": caption,
                "confidence": confidence,
                "method": "Google Lens + Enhanced AI Analysis",
                "ai_analysis": ai_analysis,
                "extracted_info": location_info,
                "raw_data": data  # For debugging
            }
            
        except Exception as e:
            return {
                "locationGuess": f"Error with Google Lens analysis: {str(e)}",
                "caption": "Google Lens analysis failed",
                "confidence": 0.0,
                "method": "Google Lens + Enhanced AI Analysis",
                "ai_analysis": {},
                "extracted_info": {},
                "raw_data": {}
            }

class ImageLocationAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the analyzer with Gemini API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze an image to identify location and provide caption using Gemini.
        """
        prompt = """You are a world-renowned expert in visual location identification with comprehensive knowledge of global landmarks, architecture, businesses, and geographical features. Your expertise spans all continents and cultures equally.

Analyze the following image and consider all visual cues without any geographical bias:

VISUAL ANALYSIS CHECKLIST:
- Architectural styles and building characteristics
- Signage, text, logos, or symbols (in any language or script)
- Vehicles, license plates, traffic signs, road markings
- Vegetation, climate indicators, geological features
- Cultural indicators, clothing, activities
- Business types, branding, interior/exterior design
- Urban planning patterns, infrastructure style
- Any visible landmarks, monuments, or distinctive features

ANALYSIS APPROACH:
1. Examine the image systematically for location clues
2. Consider multiple possibilities from different regions
3. Cross-reference visual elements for consistency
4. Provide your most confident assessment

Respond in JSON format:
{
    "locationGuess": "Your most specific location identification possible (e.g., 'Sagrada Familia, Barcelona, Spain', 'Central Park, New York, USA', 'Shibuya Crossing, Tokyo, Japan', or 'Traditional market in Southeast Asia' if specific identification isn't possible)",
    "caption": "Descriptive caption of what you see in the image",
    "confidence": 0.8,
    "visualClues": ["List of specific visual elements that led to your conclusion"],
    "alternativeLocations": ["Other possible locations if confidence is moderate"]
}

Confidence scale: 1.0 = Absolutely certain (famous landmark), 0.8+ = Very confident, 0.6+ = Moderately confident, 0.4+ = Educated guess, <0.4 = Very uncertain"""

        try:
            response = self.model.generate_content([prompt, image])
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                result["method"] = "Gemini AI Visual Analysis"
            else:
                # Fallback: parse the response manually if JSON format is not found
                result = {
                    "locationGuess": "Unable to parse location from response",
                    "caption": "Unable to parse caption from response",
                    "confidence": 0.0,
                    "method": "Gemini AI Visual Analysis",
                    "visualClues": [],
                    "alternativeLocations": []
                }
            
            return result
            
        except Exception as e:
            return {
                "locationGuess": f"Error analyzing image: {str(e)}",
                "caption": "Analysis failed",
                "confidence": 0.0,
                "method": "Gemini AI Visual Analysis",
                "visualClues": [],
                "alternativeLocations": []
            }

def get_confidence_color(confidence: float) -> str:
    """Get CSS class based on confidence level."""
    if confidence >= 0.7:
        return "confidence-high"
    elif confidence >= 0.4:
        return "confidence-medium"
    else:
        return "confidence-low"

def get_confidence_text(confidence: float) -> str:
    """Get descriptive text for confidence level."""
    if confidence >= 0.8:
        return "Very High"
    elif confidence >= 0.6:
        return "High"
    elif confidence >= 0.4:
        return "Medium"
    elif confidence >= 0.2:
        return "Low"
    else:
        return "Very Low"

def display_extracted_info(extracted_info: Dict):
    """Display extracted location information in an organized way."""
    st.markdown("#### 🔍 **Digital Footprints Found**")
    
    # Primary Locations (from Knowledge Graph)
    if extracted_info.get('primary_locations'):
        st.markdown("**📍 Primary Matches:**")
        for loc in extracted_info['primary_locations']:
            st.markdown(f'<div class="location-match">**{loc["name"]}**<br>'
                       f'Type: {loc.get("type", "Unknown")}<br>'
                       f'Description: {loc.get("description", "No description")}<br>'
                       f'Confidence: {loc.get("confidence", 0):.1%}</div>', 
                       unsafe_allow_html=True)
    
    # Businesses
    if extracted_info.get('businesses'):
        st.markdown("**🏢 Business Intel:**")
        for business in extracted_info['businesses'][:5]:  # Show top 5
            st.markdown(f"• **{business['type'].title()}**: {business['text']}")
    
    # Landmarks
    if extracted_info.get('landmarks'):
        st.markdown("**🏛️ Landmark Detection:**")
        for landmark in extracted_info['landmarks'][:5]:  # Show top 5
            st.markdown(f"• **{landmark['type'].title()}**: {landmark['text']}")
    
    # Addresses
    if extracted_info.get('addresses'):
        st.markdown("**📍 Address Traces:**")
        for address in extracted_info['addresses'][:3]:  # Show top 3
            st.markdown(f"• {address}")

def display_debug_info(image_url: str, serpapi_data: Dict, extracted_info: Dict):
    """Display debugging information."""
    st.markdown("### 🔧 **Debug Console**")
    
    # Azure Blob URL
    st.markdown("#### 📂 **Cloud Storage Evidence**")
    st.markdown('<div class="debug-section">', unsafe_allow_html=True)
    st.markdown("**Image Upload URL:**")
    st.markdown(f'<div class="url-box">{image_url}</div>', unsafe_allow_html=True)
    st.markdown(f"[🔗 View Evidence]({image_url})")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Extracted Information Summary
    st.markdown("#### 📊 **Intelligence Summary**")
    st.markdown('<div class="debug-section">', unsafe_allow_html=True)
    st.markdown(f"**Titles scraped:** {len(extracted_info.get('titles', []))}")
    st.markdown(f"**Primary locations:** {len(extracted_info.get('primary_locations', []))}")
    st.markdown(f"**Businesses identified:** {len(extracted_info.get('businesses', []))}")
    st.markdown(f"**Landmarks identified:** {len(extracted_info.get('landmarks', []))}")
    st.markdown(f"**Addresses found:** {len(extracted_info.get('addresses', []))}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # SerpAPI Response
    st.markdown("#### 🐍 **Raw Intelligence Data**")
    st.markdown('<div class="debug-section">', unsafe_allow_html=True)
    with st.expander("Show Full SerpAPI JSON Response", expanded=False):
        st.json(serpapi_data)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Extracted Information Details
    st.markdown("#### 📝 **Detailed Analysis Results**")
    st.markdown('<div class="debug-section">', unsafe_allow_html=True)
    with st.expander("Show Detailed Extracted Information", expanded=False):
        st.json(extracted_info)
    st.markdown('</div>', unsafe_allow_html=True)

def display_result(result: Dict[str, Any], title: str, tab_class: str):
    """Display analysis result in a formatted container."""
    st.markdown(f'<div class="method-tab {tab_class}">', unsafe_allow_html=True)
    st.markdown(f"### {title}")
    
    # Location guess
    st.markdown("**📍 Location Guess:**")
    st.markdown(f"<span class='neon-text'>{result['locationGuess']}</span>", unsafe_allow_html=True)
    
    # Caption
    st.markdown("**💬 What We Found:**")
    st.markdown(f"*{result['caption']}*")
    
    # Confidence
    confidence = result.get('confidence', 0)
    confidence_class = get_confidence_color(confidence)
    confidence_text = get_confidence_text(confidence)
    
    st.markdown("**🎯 Confidence Level:**")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f'<span class="{confidence_class}">{confidence:.1%}</span>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<span class="{confidence_class}">({confidence_text})</span>', unsafe_allow_html=True)
    
    st.progress(confidence)
    
    # Visual clues for Gemini analysis
    if 'visualClues' in result and result['visualClues']:
        st.markdown("**👁️ Visual Evidence:**")
        for clue in result['visualClues']:
            st.markdown(f"• {clue}")
    
    # Alternative locations
    if 'alternativeLocations' in result and result['alternativeLocations']:
        st.markdown("**🤔 Other Possibilities:**")
        for alt in result['alternativeLocations']:
            st.markdown(f"• {alt}")
    
    # Enhanced AI Analysis for Google Lens
    if 'ai_analysis' in result and result['ai_analysis']:
        ai_analysis = result['ai_analysis']
        st.markdown("**🤖 AI Detective Work:**")
        st.markdown(f"**Key Evidence:** {ai_analysis.get('primaryEvidence', 'N/A')}")
        st.markdown(f"**Investigation Notes:** {ai_analysis.get('reasoning', 'N/A')}")
        
        if ai_analysis.get('alternativeLocations'):
            st.markdown("**Alternative Leads:**")
            for alt in ai_analysis['alternativeLocations']:
                st.markdown(f"• {alt}")
    
    # Extracted information for Google Lens
    if 'extracted_info' in result and result['extracted_info']:
        display_extracted_info(result['extracted_info'])
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Title and description 
    st.markdown("<h1 class='main-header'>🕵️‍♂️ GeoGuess AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='slogan'>\"See exactly where that picture was taken\" </p>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Drop a photo. We’ll pull the thread and see where it leads. <br>Because sometimes you need to know where that coffee shop is, or... other reasons </p>", unsafe_allow_html=True)
    
 
    st.markdown('<p class="joe-quote">"A photo isn’t just a moment… it’s a map. Every shadow, every reflection—breadcrumbs leading me right to you." - Joe Goldberg</p>', unsafe_allow_html=True)

    
    # # Sidebar for configuration with enhanced styling
    # with st.sidebar:
    #     st.markdown("## ⚙️ **Setup Your Arsenal**")
        
    #     # API Keys
    #     st.markdown("### 🔑 **API Keys**")
    #     gemini_api_key = st.text_input(
    #         "🧠 Gemini AI Key:",
    #         type="password",
    #         help="Your secret weapon for AI analysis"
    #     )
        
    #     serpapi_key = st.text_input(
    #         "🔍 SerpAPI Key:",
    #         type="password",
    #         help="For that deep Google Lens investigation"
    #     )
        
    #     # Azure Storage
    #     st.markdown("### ☁️ **Cloud Storage**")
    #     azure_connection_string = st.text_input(
    #         "🗄️ Azure Connection:",
    #         type="password",
    #         help="Yep"
    #     )
        # Load API keys from environment variables
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    serpapi_key = os.getenv('SERPAPI_KEY')
    azure_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

    # Sidebar for configuration with enhanced styling
    with st.sidebar:
        st.markdown("## ⚙️ **Setup Your Arsenal**")

        
        # Analysis options
        st.markdown("### 🎯 **Investigation Methods**")
        use_gemini = st.checkbox("🧠 Deploy AI Visual Analysis", value=True)
        use_google_lens = st.checkbox("🔍 Use Reverse Image Search", value=True)
        # show_debug = st.checkbox("🐛 Show Debug Console", value=False)
        
        # Validation with fun messages
        # apis_configured = bool(gemini_api_key) if use_gemini else True
        # apis_configured = apis_configured and (bool(serpapi_key and azure_connection_string) if use_google_lens else True)
        
        # if apis_configured:
        #     st.markdown('<div class="success-message">✅ All systems are GO! 🚀</div>', unsafe_allow_html=True)
        # else:
        #     st.markdown('<div class="warning-message">⚠️ Need those keys to work our magic! 🔮</div>', unsafe_allow_html=True)
        
        # Validation with fun messages
        apis_configured = bool(gemini_api_key) if use_gemini else True
        apis_configured = apis_configured and (bool(serpapi_key and azure_connection_string) if use_google_lens else True)
        
        if apis_configured:
            st.markdown('<div class="success-message">✅ All systems are GO! 🚀</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-message">⚠️ Environment variables not configured! 🔮</div>', unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("### 🎭 **How We Operate:**")
        
        # Feature cards with enhanced styling
        st.markdown("""
        <div class="feature-card">
            <div class="emoji-large">🧠</div>
            <strong>AI Visual Analysis</strong><br>
            Our AI examines every pixel, sign, and shadow to pinpoint locations with scary accuracy
        </div>
        
        <div class="feature-card">
            <div class="emoji-large">🔍</div>
            <strong>Reverse Image Hunt</strong><br>
            We search the entire internet to find similar images and extract location intelligence
        </div>
        
        <div class="feature-card">
            <div class="emoji-large">🌍</div>
            <strong>Global Coverage</strong><br>
            From Tokyo alleys to NYC rooftops - nowhere can hide from our algorithms
        </div>
        """, unsafe_allow_html=True)
    
    # # Main content area
    # if not apis_configured:
    #     st.markdown("### 🚫 **Hold Up!**")
    #     st.info("Configure those API keys in the sidebar first. Even digital stalkers need proper tools! 😉")
    #     return

    # Main content area
    if not apis_configured:
        st.markdown("### 🚫 **Hold Up!**")
        st.info("Environment variables not configured! Make sure your .env file contains the required API keys. 😉")
        return
    
    # Initialize services
    analyzers = {}
    
    if use_gemini and gemini_api_key:
        try:
            analyzers['gemini'] = ImageLocationAnalyzer(gemini_api_key)
            st.success("🧠 AI Detective: **ONLINE**")
        except Exception as e:
            st.error(f"🚨 AI Detective failed to boot: {str(e)}")
    
    if use_google_lens and serpapi_key and azure_connection_string:
        try:
            analyzers['azure'] = AzureBlobManager(azure_connection_string)
            # Pass Gemini model to Google Lens analyzer for enhanced analysis
            gemini_model = analyzers.get('gemini', {}).model if 'gemini' in analyzers else None
            analyzers['google_lens'] = GoogleLensAnalyzer(serpapi_key, gemini_model)
            st.success("🔍 Internet Sleuth: **READY**")
        except Exception as e:
            st.error(f"🚨 Internet Sleuth malfunctioned: {str(e)}")
    
    # File upload with enhanced styling
    st.markdown("### 📸 **Drop Your Evidence**")
    
    # Custom upload area
    uploaded_file = st.file_uploader(
        "",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        help="Upload any image and let us work our magic ✨",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### 🖼️ **Target Image**")
            # Display the image
            image = Image.open(uploaded_file)
            st.image(image, caption="Evidence Submitted", use_column_width=True)
            
            # Image info with enhanced styling
            st.markdown(f"**📄 File:** `{uploaded_file.name}`")
            st.markdown(f"**📏 Dimensions:** `{image.size[0]} x {image.size[1]}px`")
            st.markdown(f"**💾 Size:** `{uploaded_file.size:,} bytes`")
        
        with col2:
            st.markdown("### 🎯 **Investigation Dashboard**")
            
            # Enhanced analyze button
            if st.button("🚀 **START INVESTIGATION**", key="analyze_btn"):
                results = {}
                image_url = None
                serpapi_data = {}
                extracted_info = {}
                
                # Gemini Analysis with enhanced loading message
                if 'gemini' in analyzers:
                    with st.spinner("🧠 AI is scanning every pixel... This might take a moment"):
                        results['gemini'] = analyzers['gemini'].analyze_image(image)
                
                # Google Lens Analysis with enhanced loading messages
                if 'google_lens' in analyzers and 'azure' in analyzers:
                    with st.spinner("☁️ Processing..."):
                        try:
                            # Upload image to Azure
                            image_url = analyzers['azure'].upload_image(image)
                            st.success(f"✅ Evidence uploaded successfully!")
                            
                        except Exception as e:
                            st.error(f"🚨 Upload failed: {str(e)}")
                    
                    if image_url:
                        with st.spinner("🔍 Searching the entire internet for matches..."):
                            try:
                                # Analyze with Google Lens
                                results['google_lens'] = analyzers['google_lens'].analyze_image_url(image_url)
                                
                                # Extract debug data
                                serpapi_data = results['google_lens'].get('raw_data', {})
                                extracted_info = results['google_lens'].get('extracted_info', {})
                                
                            except Exception as e:
                                st.error(f"🚨 Internet search failed: {str(e)}")
                                results['google_lens'] = {
                                    "locationGuess": f"Investigation failed: {str(e)}",
                                    "caption": "Something went wrong in our digital hunt",
                                    "confidence": 0.0,
                                    "method": "Google Lens + AI Analysis"
                                }
                
                # Display results with enhanced styling
                st.markdown("## 📊 **Investigation Results**")
                
                if 'gemini' in results:
                    display_result(results['gemini'], "🧠 AI Detective Report", "gemini-tab")
                
                if 'google_lens' in results:
                    display_result(results['google_lens'], "🔍 Internet Sleuth Report", "googlelens-tab")
                
                # Debug Information
                # if show_debug and (image_url or serpapi_data or extracted_info):
                #     display_debug_info(image_url or "Not available", serpapi_data, extracted_info)
                
                # Comparison and recommendation with enhanced styling
                if len(results) > 1:
                    st.markdown("### 🏆 **Final Verdict**")
                    gemini_conf = results.get('gemini', {}).get('confidence', 0)
                    lens_conf = results.get('google_lens', {}).get('confidence', 0)
                    
                    if gemini_conf > lens_conf:
                        st.markdown('<div class="success-message">🧠 <strong>AI Detective wins!</strong> Higher confidence in visual analysis.</div>', unsafe_allow_html=True)
                    elif lens_conf > gemini_conf:
                        st.markdown('<div class="success-message">🔍 <strong>Internet Sleuth wins!</strong> Found better matches online.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="warning-message">🤝 <strong>It\'s a tie!</strong> Both methods show similar confidence.</div>', unsafe_allow_html=True)
                
                # Enhanced tips based on results
                max_confidence = max([r.get('confidence', 0) for r in results.values()] + [0])
                if max_confidence < 0.5:
                    st.markdown("### 💡 **Pro Stalker Tips**")
                    st.warning("**Low confidence detected!** For better results, try images with:")
                    st.markdown("""
                    - 🏪 **Clear storefront signs** or business names
                    - 🏛️ **Famous landmarks** in the background  
                    - 🚗 **License plates** or street signs
                    - 🌅 **Good lighting** and sharp image quality
                    - 📱 **Recent photos** work better than old ones
                    """)
                
                # Fun success message
                if max_confidence > 0.8:
                    st.balloons()
                    st.success("🎉 **Investigation successful!** We've cracked this case wide open!")
    
    # Footer with enhanced styling and fun copy
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem;">
            <p style="color: #a8a8b3; font-size: 1.1rem;">
                Built with 💜 by digital detectives who understand that curiosity never killed the cat... 
                it just made it better at finding things 😏
            </p>
            <p style="color: #666; font-size: 0.9rem;">
                Powered by Wali • Gemini AI • Google Lens • Azure Cloud
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()