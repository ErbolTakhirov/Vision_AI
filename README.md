# Vision AI Assistant 👁️

A powerful, locally-hosted **Telegram Mini App** designed to assist visually impaired users. This project leverages state-of-the-art **Open Source AI models** to provide a real-time "Second Sight" experience directly from a smartphone.

## ✨ Features

*   **Hands-Free Voice Control**: Activate the assistant by saying **"Hey Vision"** or **"Vision"**. No need to press buttons.
*   **Smart Vision (BLIP + LLM)**: Analyzes photos and answers questions about them in natural language (e.g., "What is in front of me?", "Describe the scene").
*   **Navigator Mode**: A toggleable mode that continuously scans the environment (every 3.5s) and announces detected objects (using fast YOLOv8) to help with navigation.
*   **Reading Mode (OCR)**: Automatically detects and reads text from images (documents, signs, screens) using **EasyOCR**.
*   **Local Processing**: Most AI tasks (Speech-to-Text, Object Detection, Image Captioning) run **locally** on the host machine for privacy and speed.
*   **Natural Voice (TTS)**: High-quality Russian voice synthesis using MS Edge TTS.
*   **Memory (RAG Lite)**: The assistant remembers user context and conversation history for more natural interactions.
*   **Sound Design**: Audio cues (beeps, haptic feedback) for actions like listening, analyzing, or errors.

## 🛠️ Tech Stack

*   **Backend**: Django (Python)
*   **Frontend**: HTML5, CSS3, Vanilla JS (Telegram Web SDK)
*   **AI Models**:
    *   **LLM**: DeepSeek / OpenRouter (via OpenAI API compatibility)
    *   **Vision**: BLIP (Salesforce)
    *   **Object Detection**: YOLOv8 (Ultralytics)
    *   **OCR**: EasyOCR
    *   **Speech-to-Text**: Faster-Whisper (Local)
    *   **Text-to-Speech**: Edge-TTS
*   **Database**: SQLite (default) / PostgreSQL compatible

## 🚀 Installation & Setup

### Prerequisites
*   Python 3.8+
*   CUDA-capable GPU (Recommended for faster inference)
*   Telegram Bot Token

### 1. Clone the repository
```bash
git clone https://github.com/your-username/vision-ai-assistant.git
cd vision-ai-assistant
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# For GPU support (Recommended):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Configure Environment
Create a `.env` file in the root directory:
```ini
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,your-ngrok-domain.ngrok-free.dev

# Telegram Settings
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
WEBAPP_URL=https://your-ngrok-domain.ngrok-free.dev

# AI Provider API Key (DeepSeek or OpenRouter)
OPENAI_API_KEY=your_api_key
```

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Run the Server
```bash
python manage.py runserver
```

## 📱 Running the Mini App

1.  Expose your local server to the internet (required for Telegram Web Apps) using **ngrok**:
    ```bash
    ngrok http 8000
    ```
2.  Update `WEBAPP_URL` in `.env` with your new ngrok HTTPS URL.
3.  Open your Telegram Bot (`bot.py` or configured via BotFather) and launch the Web App.
4.  **Grant Microphone / Camera permissions** in the browser when prompted.

## 🕹️ Usage

*   **Chat Mode**: Say "Hey Vision, what do you see?" or press the button manually.
*   **Navigator Mode**: Flip the toggle at the top right. Point your phone, and it will list objects around you.
*   **Text Reading**: Just show a document and ask "Read this text".


