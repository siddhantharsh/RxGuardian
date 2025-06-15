# RxGuardian

RxGuardian is an AI-powered prescription analysis tool that helps users understand their prescriptions and find safer alternatives.

## Features

- Analyze prescription text for potential issues
- Check for overdose risks
- Suggest cheaper alternatives
- Consider patient conditions and diagnosis
- Modern, user-friendly interface

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/RxGuardian.git
cd RxGuardian
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Running the Application

1. Start the Flask server:
```bash
python backend/app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Enter your prescription text in the main text area
2. Optionally provide your diagnosed disease
3. Optionally add any special conditions or allergies
4. Click "Analyze Prescription" to get results

## Technology Stack

- Backend: Python with Flask
- Frontend: Vanilla JavaScript with modern CSS
- AI: Google's Gemini API

## License

MIT License 