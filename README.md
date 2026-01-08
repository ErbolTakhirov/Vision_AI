# WayFinder

**High-Performance AI Vision & Navigation Assistant**

WayFinder is an advanced, real-time AI assistant capable of seeing, hearing, and guiding users. It combines state-of-the-art computer vision models, ultra-fast speech recognition, and intelligent navigation into a seamless experience.

## key Features

### 🚀 Ultra-Fast Performance
- **Parallel Processing**: Simultaneous audio and visual analysis for instant feedback.
- **Optimized AI Stack**: Uses **Whisper Tiny** for millisecond-latency speech recognition and **YOLOv8 Nano** for rapid object detection.
- **Smart Resource Management**: Intelligent image downscaling (640px) reduces latency by up to 300% without losing accuracy.
- **Edge TTS**: High-quality, natural-sounding voice generation powered by Microsoft Edge cloud APIs.

### 🧠 Intelligent Capabilities
- **Eyes & Ears**:
  - **Vision**: Analyzes surroundings using **BLIP** (Scene Understanding) and **YOLOv8** (Object Detection).
  - **Hearing**: Listens for the wake word **"WayFinder"** (powered by Porcupine) for hands-free operation.
  - **Reading**: Extracts text from the environment using **EasyOCR**.
- **Contextual Awareness**: Remembers conversation history and adapts responses to the user's profile using the **CAG (Context-Affect-Guidance) System**.

### 📱 Applications
- **Smart Navigation**: Extracts destinations from voice commands and builds routes.
- **Visual Assistant**: Describes scenes, reads signs, and identifies objects in real-time.
- **Interactive Chat**: Full-duplex conversation with visual context awareness.

---

## Tech Stack

### Backend
- **Core**: Django 6.0 (Asynchronous)
- **AI Models**:
  - **STT**: Faster-Whisper (Tiny/Int8)
  - **Vision**: Salesforce BLIP, Ultralytics YOLOv8, EasyOCR
  - **LLM Integration**: DeepSeek / OpenAI API
  - **Wake Word**: Picovoice Porcupine (Server-side & Mobile)
- **Database**: PostgreSQL / SQLite

### Mobile (Flutter)
- **Framework**: Flutter 3.x
- **Navigation**: Geolocator, OpenRouteService
- **Voice**: Porcupine Wake Word Engine
- **UI**: Material Design 3 with Dark Mode

---

## Installation & Setup

### 1. Backend Setup (Windows/Linux)

```bash
# Clone repository
git clone <your-repo-url>
cd WayFinder

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies (ensure Pytorch is installed for your CUDA version if available)
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your keys: OPENAI_API_KEY, PICOVOICE_ACCESS_KEY, etc.

# Run migrations and start server
python manage.py migrate
python manage.py runserver
```

### 2. Mobile Setup

```bash
cd vision_mobile

# Install packages
flutter pub get

# Run on connected device
flutter run
```

---

## Wake Word Configuration

The system uses **Porcupine** for wake word detection.
- **Wake Phrase**: "Way Finder"
- **Files**:
  - Windows: `Way-Finder_en_windows_v4_0_0.ppn` (Server-side listening)
  - Android: `assets/models/way_finder_android.ppn` (Mobile listening)

Ensure `PICOVOICE_ACCESS_KEY` is set in your `.env` file for this feature to work.

---

## Usage

1. **Start the App/Server**: Ensure both backend and mobile app are running.
2. **Say "WayFinder"**: The system will wake up and listen for your command.
3. **Voice Commands**:
   - *"What is in front of me?"*
   - *"Read this text."*
   - *"How do I get to [Street Name]?"*
   - *"Where am I?"*

---

*Project maintained by the developer. No external liabilities.*
