from flask import Flask, request, jsonify, render_template, send_file
from fpdf import FPDF
import io
import os
import re
import json
from dotenv import load_dotenv
import logging
import json
import google.generativeai as genai
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    logger.error("No GOOGLE_API_KEY found in environment variables")
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

logger.info("Configuring Gemini API...")
genai.configure(api_key=api_key)

# Rate limiting configuration
RATE_LIMIT_PER_MINUTE = 30  # Adjust based on your quota
RATE_LIMIT_PER_DAY = 1000   # Adjust based on your quota
request_timestamps = []

def check_rate_limit():
    """Check if we're within rate limits"""
    global request_timestamps
    now = datetime.now()
    
    # Remove timestamps older than 24 hours
    request_timestamps = [ts for ts in request_timestamps if now - ts < timedelta(days=1)]
    
    # Check daily limit
    if len(request_timestamps) >= RATE_LIMIT_PER_DAY:
        return False, "Daily request limit reached. Please try again tomorrow."
    
    # Check per-minute limit
    recent_requests = [ts for ts in request_timestamps if now - ts < timedelta(minutes=1)]
    if len(recent_requests) >= RATE_LIMIT_PER_MINUTE:
        return False, "Rate limit reached. Please wait a minute before trying again."
    
    # Add current request timestamp
    request_timestamps.append(now)
    return True, None

# List available models
logger.info("Listing available models...")
available_models = []
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        available_models.append(m.name)
        logger.info(f"Found model: {m.name}")

# Try different models in order of preference
models_to_try = [
    'models/gemini-1.5-flash',
    'models/gemini-1.5-flash-latest',
    'models/gemini-1.5-pro',
    'models/gemini-1.5-pro-latest'
]

model = None
for model_name in models_to_try:
    if model_name in available_models:
        logger.info(f"Using model: {model_name}")
        model = genai.GenerativeModel(model_name)
        break

if not model:
    logger.error("No suitable model found")
    raise ValueError("No suitable Gemini model found")

app = Flask(__name__, static_folder='static', template_folder='templates')

def create_pdf_analysis(analysis):
    """Create a PDF document from the analysis data with improved styling and layout"""
    try:
        # Initialize PDF with better defaults
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(left=15, top=15, right=15)
        pdf.add_page()
        
        # Set compression
        pdf.set_compression(True)
        
        # Set up fonts with fallbacks
        try:
            pdf.add_font('Arial', '', 'c:/windows/fonts/arial.ttf', uni=True)
            pdf.add_font('Arial', 'B', 'c:/windows/fonts/arialbd.ttf', uni=True)
            pdf.add_font('Arial', 'I', 'c:/windows/fonts/ariali.ttf', uni=True)
            pdf.add_font('Arial', 'BI', 'c:/windows/fonts/arialbi.ttf', uni=True)
        except:
            # Fallback to default font if Arial is not available
            pass
        
        # Set default font
        pdf.set_font('Arial', '', 10)
        
        # Add header with logo and title
        # Title with better styling
        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(44, 62, 80)  # Dark blue-gray
        pdf.cell(0, 10, "RxGuardian", 0, 1, 'C')
        
        # Subtitle
        pdf.set_font('Arial', 'I', 12)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, "Prescription Analysis Report", 0, 1, 'C')
        
        # Divider line
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
        
        # Report metadata
        pdf.ln(8)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 0, 1)
        pdf.cell(0, 5, f"Analyzed {len(analysis)} medications", 0, 1)
        
        # Add some space before content
        pdf.ln(5)
        
        # Set smaller font for content
        pdf.set_font('Arial', '', 10)
        
        # Calculate available height (A4: 297mm, 1mm = 3.78 units)
        available_height = 250  # 297mm - margins
        content_height = 0
        
        # Analysis content in a single column
        for idx, med in enumerate(analysis):
            # Calculate required height for this medication
            med_height = 16  # Base height for header and basic info
            
            # Estimate height for reasoning
            if 'reasoning' in med and med['reasoning']:
                # Estimate lines for reasoning (approx 80 chars per line)
                med_height += max(1, len(str(med['reasoning'])) // 80) * 5 + 8
                
            # Estimate height for alternatives
            if 'cheaper_alternatives' in med and med['cheaper_alternatives']:
                med_height += len(med['cheaper_alternatives']) * 6 + 8
                
            # Add height for recommended dose if present
            if 'recommended_dose' in med and med['recommended_dose']:
                med_height += 6
                
            # Add some padding
            med_height += 10
            
            # Check if we need a new page (with margin)
            if pdf.get_y() + med_height > 270:  # Leave some margin at bottom
                pdf.add_page()
            
            y_start = pdf.get_y()
            
            # Draw medication card with subtle shadow and border
            pdf.set_line_width(0.2)
            
            # Shadow (only if not at the bottom of the page)
            if y_start + med_height < 270:  # Leave room for footer
                pdf.set_fill_color(220, 220, 220)
                pdf.rect(12, y_start + 2, 190, med_height, 'F')
            
            # Card background
            pdf.set_fill_color(255, 255, 255)  # White background
            pdf.set_draw_color(200, 200, 200)  # Light border
            pdf.rect(10, y_start, 190, med_height, 'FD')
            
            # Add accent color bar on the left
            pdf.set_fill_color(255, 107, 107)  # Primary color
            pdf.rect(10, y_start, 4, med_height, 'F')
            
            # Medication header with better typography
            pdf.set_xy(20, y_start + 8)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(44, 62, 80)  # Dark blue-gray
            pdf.cell(0, 8, med.get('medication_name', 'Unnamed Medication'), 0, 1)
            
            # Divider line under header
            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, y_start + 18, 195, y_start + 18)
            
            # Details row with icons (using text as icons for simplicity)
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(100, 100, 100)
            
            # Prescribed dose
            pdf.set_xy(20, y_start + 22)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(25, 6, "Dose:")
            pdf.set_font('Arial', '', 9)
            pdf.cell(40, 6, med.get('prescribed_dose', 'N/A'))
            
            # Frequency
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(25, 6, "Frequency:")
            pdf.set_font('Arial', '', 9)
            pdf.cell(0, 6, med.get('frequency', 'N/A'), 0, 1)
            
            # Cost with colored text
            pdf.set_xy(20, y_start + 30)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(25, 6, "Cost:")
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(255, 107, 107)  # Primary color for cost
            pdf.cell(0, 6, f"Rs. {med.get('prescribed_cost', 'N/A')}", 0, 1)
            pdf.set_text_color(100, 100, 100)  # Reset text color
            
            # Recommended dose if available (with checkmark icon)
            if 'recommended_dose' in med and med['recommended_dose']:
                pdf.set_xy(20, pdf.get_y() + 2)
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(0, 128, 0)  # Green for recommendations
                pdf.cell(30, 6, "✓ Recommended:")
                pdf.set_font('Arial', '', 9)
                pdf.cell(0, 6, med['recommended_dose'], 0, 1)
                pdf.set_text_color(100, 100, 100)  # Reset text color
            
            # Reasoning with better formatting
            if 'reasoning' in med and med['reasoning']:
                pdf.set_xy(20, pdf.get_y() + 4)
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(44, 62, 80)  # Darker text for headings
                pdf.cell(0, 6, "Analysis:", 0, 1)
                
                pdf.set_xy(25, pdf.get_y() + 1)
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(80, 80, 80)  # Slightly darker for better readability
                
                # Split reasoning into sentences for better formatting
                reasoning = str(med['reasoning']).replace('•', '• ').replace('\n', ' ').strip()
                pdf.multi_cell(165, 4.5, reasoning)
                pdf.set_text_color(100, 100, 100)  # Reset text color
            
            # Alternatives with better formatting
            if 'cheaper_alternatives' in med and med['cheaper_alternatives']:
                pdf.set_xy(20, pdf.get_y() + 2)
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(0, 128, 0)  # Green for savings
                pdf.cell(0, 6, "Cheaper Alternatives:", 0, 1)
                
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(80, 80, 80)  # Slightly darker for better readability
                
                for alt in med['cheaper_alternatives']:
                    pdf.set_xy(25, pdf.get_y() + 2)
                    # Use bullet point with better spacing
                    alt_text = f"• {alt.get('name', 'N/A')} - "
                    pdf.cell(100, 6, alt_text)
                    
                    # Price with color coding
                    pdf.set_text_color(255, 107, 107)  # Primary color for price
                    pdf.cell(30, 6, f"Rs. {alt.get('cost', 'N/A')}")
                    
                    # Availability
                    if 'availability' in alt:
                        pdf.set_text_color(100, 100, 100)
                        pdf.cell(0, 6, f"({alt['availability']})")
                    pdf.ln(4)
            
            # Add some space after each medication
            pdf.set_xy(10, pdf.get_y() + 8)
            
            # Add page number footer if we're at the bottom
            if pdf.get_y() > 270 and idx < len(analysis) - 1:
                pdf.add_page()
        
        # Add footer with page numbers
        total_pages = pdf.page_no()
        for i in range(1, total_pages + 1):
            # Switch to the page
            pdf.page = i
            
            # Save current position
            x = pdf.get_x()
            y = pdf.get_y()
            
            # Set font for footer
            pdf.set_font('Arial', 'I', 8)
            pdf.set_text_color(150, 150, 150)
            
            # Draw footer line
            pdf.line(10, 287, 200, 287)
            
            # Add page number
            pdf.set_xy(0, 288)
            pdf.cell(0, 10, f"Page {i} of {total_pages}", 0, 0, 'C')
            
            # Restore position
            pdf.set_xy(x, y)
        
        return pdf
    except Exception as e:
        logger.error(f"Error in create_pdf_analysis: {str(e)}")
        raise

@app.route('/download', methods=['POST'])
def download_analysis():
    try:
        analysis = request.json.get('analysis')
        if not analysis:
            return jsonify({'error': 'No analysis data provided'}), 400
            
        pdf = create_pdf_analysis(analysis)
        
        # Create a bytes buffer for the PDF
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        
        # Create a file-like object in memory
        pdf_io = io.BytesIO(pdf_bytes)
        
        # Return the file directly from memory
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'prescription_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

def analyze_prescription_with_ai(text):
    try:
        print(f"Analyzing prescription text: {text[:200]}...")  # Log first 200 chars of input
        
        if not text or not isinstance(text, str) or not text.strip():
            logger.error("Invalid or empty prescription text provided")
            return [{"medication_name": "Error", "reasoning": "Invalid or empty prescription text provided"}]
            
        can_proceed, error_message = check_rate_limit()
        if not can_proceed:
            error_msg = f"Rate limit exceeded: {error_message}"
            print(error_msg)
            return [{"medication_name": "Rate Limit", "reasoning": error_msg}]

        prompt = f"""You are a professional Indian pharmacist analyzing a prescription. Analyze this prescription and provide detailed analysis in JSON format:

Prescription Text:
{text}

Output format:
[
    {{
        "medication_name": "Medication Name",
        "prescribed_dose": "Dose",
        "frequency": "Frequency",
        "overdose": true/false,
        "reasoning": "Detailed reasoning about safety, contraindications, etc.",
        "prescribed_cost": "Approximate cost in Indian Rupees (Rs.)",
        "recommended_dose": "Recommended dose based on WHO and Indian guidelines",
        "cheaper_alternatives": [
            {{
                "name": "Alternative Name",
                "cost": "Approximate cost in Indian Rupees (Rs.)",
                "reason": "Why this alternative is recommended",
                "availability": "Widely available in India / Limited availability"
            }}
        ]
    }}
]

Key points to consider:
1. Use WHO Essential Medicines List and Indian National List of Essential Medicines (NLEM) guidelines
2. For cost comparisons:
   - Provide exact Indian market prices in Rs.
   - Compare with specific brands from different pharmaceutical companies
   - Do not recommend the same medicine as an alternative
   - If no cheaper alternative is available, explicitly state "No cheaper alternative available in India"
3. For alternatives:
   - Suggest specific brands from different manufacturers (e.g., Cipla, Ranbaxy, Sun Pharma, Dr. Reddy's)
   - Consider bioequivalence and therapeutic equivalence
   - Include fixed-dose combinations where applicable
   - Check availability in Indian pharmacies
4. For each medication:
   - Compare prescribed dose with WHO/Indian recommended doses
   - Consider patient's age, weight, and condition
   - Check for contraindications specific to Indian population
   - Provide exact cost information based on Indian market prices
   - Suggest alternatives that are commonly available in Indian pharmacies
5. Format the output in a professional, easy-to-read manner
6. Include specific brand names commonly used in India
7. Consider Indian healthcare system's drug availability and pricing
8. If no cheaper alternative exists:
   - State "No cheaper alternative available in India"
   - Explain why (e.g., single-source drug, patent protection, etc.)
   - Suggest dosage adjustments if applicable
   - Provide information about generic availability

Specific brand recommendations:
- For Metformin: Suggest brands like Glycomet (Cipla), Glucomet (Ranbaxy), or Glim (Sun Pharma)
- For Atorvastatin: Suggest brands like Atorva (Cipla), Atorlip (Dr. Reddy's), or Lipitor (Pfizer)
- For Amlodipine: Suggest brands like Amlovas (Cipla), Stamlor (Ranbaxy), or Amlokind (Sun Pharma)
- For Acetaminophen: Suggest brands like Crocin (GSK), Calpol (GSK), or Paracetamol (various generics)
- For Pantoprazole: Suggest brands like Pantocid (Cipla), Pantop (Ranbaxy), or Pantozole (Sun Pharma)
- For Vitamin D3: Suggest brands like D3 (Cipla), D3 (Ranbaxy), or D3 (Sun Pharma)
- For Aspirin: Suggest brands like Aspro (GSK), Aspirin (Bayer), or Aspirin (various generics)

Remember to:
- Never recommend the same brand as an alternative
- Always suggest different manufacturers' brands
- Provide exact pricing for each specific brand
- Include manufacturer name with each recommendation
- If no cheaper alternative exists from a different manufacturer, state "No cheaper alternative available in India"
"""

        logger.info("Sending analysis request to AI")
        try:
            response = model.generate_content(prompt)
            logger.info(f"Received AI response: {response}")
            if not response or not hasattr(response, 'text') or not response.text:
                logger.error("Invalid or empty response from AI model")
                return [{"medication_name": "Error", "reasoning": "Received an invalid response from the AI model"}]
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return [{"medication_name": "Error", "reasoning": f"Error communicating with AI model: {str(e)}"}]
        
        try:
            # Log the full response for debugging
            logger.info(f"Full AI response: {response.text}")
            
            # Look for JSON in multiple formats
            json_str = None
            
            # Try to find JSON in code block first (```json ... ```)
            json_start = response.text.find('```json')
            if json_start == -1:
                json_start = response.text.find('```')  # Try without 'json' specifier
                if json_start != -1:
                    json_start += 3  # Skip the opening ```
            else:
                json_start += 7  # Skip ```json
                
            if json_start != -1:
                json_end = response.text.find('```', json_start)
                if json_end == -1:  # If no closing ```, try to find the end of the JSON
                    json_end = response.text.rfind('}')
                    if json_end > json_start:
                        json_end += 1  # Include the closing brace
                
                if json_end > json_start:
                    json_str = response.text[json_start:json_end].strip()
            
            # If not found in code block, try to find JSON directly
            if not json_str:
                json_start = response.text.find('{')
                json_end = response.text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response.text[json_start:json_end].strip()
            
            if json_str:
                # Clean up JSON string - be more careful with replacements
                json_str = json_str.strip()
                logger.info(f"Raw JSON string: {json_str}")
                
                # Try multiple parsing strategies
                for attempt in [
                    lambda s: json.loads(s),  # Try as-is first
                    lambda s: json.loads(s.replace("'", '"')),  # Try with single quotes replaced
                    lambda s: json.loads(re.sub(r"(\w+)\s*:", r'"\1":', s.replace("'", '"'))),  # Try to fix unquoted keys
                ]:
                    try:
                        analysis = attempt(json_str)
                        logger.info(f"Successfully parsed AI response using {attempt.__name__}")
                        return analysis
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.warning(f"Parsing attempt failed: {str(e)}")
                        continue
                
                # If we get here, all parsing attempts failed
                logger.error(f"All JSON parsing attempts failed for: {json_str}")
                return [{"medication_name": "Error", "reasoning": "Could not parse the AI response as valid JSON"}]
            else:
                logger.error("Could not find JSON in AI response")
                return [{"medication_name": "Error", "reasoning": "Could not find JSON in AI response"}]
                
        except Exception as e:
            error_msg = f"Error processing AI response: {str(e)}"
            logger.error(error_msg)
            return [{"medication_name": "Error", "reasoning": error_msg}]
    except Exception as e:
        logger.error(f"Error analyzing prescription: {str(e)}")
        return [{"medication_name": "Error", "reasoning": f"Error analyzing prescription: {str(e)}"}]

def add_default_values(analysis):
    """Add default values to ensure all required fields are present"""
    if not isinstance(analysis, list):
        analysis = [analysis]
        
    for i, med in enumerate(analysis):
        if not isinstance(med, dict):
            med = {'medication_name': str(med)}
        med.setdefault('medication_name', 'Unknown')
        med.setdefault('prescribed_dose', 'Not specified')
        med.setdefault('frequency', 'Not specified')
        med.setdefault('overdose', False)
        med.setdefault('reasoning', 'No reasoning provided')
        med.setdefault('prescribed_cost', 'Not specified')
        med.setdefault('recommended_dose', 'Not specified')
        med.setdefault('cheaper_alternatives', [])
        analysis[i] = med
    return analysis

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_prescription():
    try:
        logger.info("Received request to /analyze endpoint")
        data = request.get_json(silent=True)
        
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400
            
        logger.info(f"Received data: {data}")
            
        if 'prescription' not in data or not data['prescription'].strip():
            logger.error("No prescription text provided")
            return jsonify({'error': 'No prescription text provided'}), 400
            
        text = data['prescription'].strip()
        logger.info(f"Analyzing prescription text: {text[:100]}...")

        # Analyze with AI
        logger.info("Calling analyze_prescription_with_ai")
        analysis = analyze_prescription_with_ai(text)
        logger.info(f"Received analysis: {analysis}")
        
        # Ensure analysis is a list
        if not isinstance(analysis, list):
            analysis = [analysis]
            
        # Ensure each medication has all required fields
        for i, med in enumerate(analysis):
            if not isinstance(med, dict):
                med = {'medication_name': str(med)}
            med.setdefault('medication_name', 'Unknown')
            med.setdefault('prescribed_dose', 'Not specified')
            med.setdefault('frequency', 'Not specified')
            med.setdefault('overdose', False)
            med.setdefault('reasoning', 'No reasoning provided')
            med.setdefault('prescribed_cost', 'Not specified')
            med.setdefault('recommended_dose', 'Not specified')
            med.setdefault('cheaper_alternatives', [])
            analysis[i] = med  # Update the list with the processed medication
            
        response_data = {
            'analysis': analysis
        }
        print("Sending response:", response_data)
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in analyze_prescription: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)