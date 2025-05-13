# Video Transcription Web Application

This project is a Flask-based web application that allows users to upload a video file, extract its audio, transcribe the audio using OpenAI's Whisper model, and generate a WebVTT file with speaker placeholders. Additionally, the app performs speaker diarization via `pyannote.audio` and provides an interface for previewing the video with the generated subtitles, as well as editing the speaker names before downloading the final files.

## Features

- **Video Upload**: Upload a video file through the web interface.
- **Audio Extraction**: Uses `ffmpeg` to extract audio from the video.
- **Speech Transcription**: Transcribes the audio using OpenAI's Whisper (using the `medium.en` model by default).
- **Speaker Diarization**: Uses `pyannote.audio` to identify different speakers and assign them placeholder labels (e.g., `[SPEAKER_01]`, `[SPEAKER_02]`).
- **Editable Subtitles**: Provides a preview of the video with subtitles and a form to update speaker names.
- **Downloadable Files**: Allows users to download the final WebVTT file and a plain text transcript.

## Requirements

- **Python 3.7+**
- **Flask** – Web framework for Python.
- **ffmpeg** – Must be installed and available in the system PATH.
- **OpenAI Whisper** – For speech transcription. Install via:
  ```bash
  pip install openai-whisper
  ```
- **PyTorch** – Required by Whisper (install a GPU-enabled version if available).
- **pyannote.audio** – For speaker diarization. Install via:
  ```bash
  pip install pyannote.audio
  ```
- **Hugging Face Access Token** – Required to load the `pyannote/speaker-diarization` model. Replace the placeholder in `app.py` with your token.
- **UIKit** – Frontend CSS framework loaded via CDN in the HTML templates.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create a Virtual Environment and Activate It:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   ```

3. **Install the Required Packages:**
   ```bash
   pip install Flask openai-whisper pyannote.audio
   ```
   Ensure that you have the appropriate version of PyTorch installed.

4. **Install ffmpeg:**
   - On Ubuntu: `sudo apt install ffmpeg`
   - On Windows: Download from [ffmpeg.org](https://ffmpeg.org/) and add it to your system PATH.

5. **Configure Your Hugging Face Token:**
   - Open `app.py` and replace `"YOUR_HF_TOKEN"` with your actual Hugging Face access token.

## Usage

1. **Run the Application:**
   ```bash
   python app.py
   ```

2. **Access the Web Interface:**
   - Open your browser and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

3. **Upload and Process a Video:**
   - Use the provided form (with your updated `index.html`) to upload a video.
   - The application will extract the audio, perform speaker diarization and transcription, and generate a WebVTT file with speaker placeholders.

4. **Edit Speaker Names:**
   - After processing, the app displays a preview of the video (with the generated subtitles attached) on the left and a form on the right.
   - Update the speaker placeholders (e.g., `[SPEAKER_01]`) with the actual speaker names.

5. **Download the Final Files:**
   - After updating, download the final WebVTT file and the transcript from the final page.

## Project Structure

```
myapp/
├── app.py             # Main Flask application code.
├── templates/
│   ├── index.html     # Upload form (updated version provided by the user).
│   ├── edit.html      # Speaker name editing and video preview page.
│   └── final.html     # Final download links for WebVTT and transcript.
├── README.md          # This file.
└── .gitignore         # Git ignore file.
```

## Notes

- **Temporary Files:** Uploaded video files are stored in the system's temporary directory for preview purposes. Consider implementing a cleanup strategy for production.
- **Error Handling:** If speaker diarization fails, the app will default to using "Unknown" as the speaker label.
- **Scalability:** This project is intended as a proof-of-concept. For production use, consider background task queues (e.g., Celery) and persistent storage solutions.

## License

This project is licensed under the MIT License.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio)
- [UIKit](https://getuikit.com/)
- [Marmot Library Network](https://marmot.org)