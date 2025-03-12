import os
import uuid
import io
import subprocess
import tempfile
from flask import Flask, render_template, request, send_file, url_for, redirect
import whisper

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1000  # up to 1G uploads

# Load the Whisper model (using medium.en in this example; change as needed)
model = whisper.load_model("medium.en")

# Dictionary to store generated files and info per job id.
# For each uid we store: vtt (str), transcript (str), video_path (str), placeholder_map (dict)
generated_files = {}

def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS.mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def get_speaker_for_segment(diarization, start, end):
    """Determine the speaker for a segment using diarization. Returns a string label."""
    mid_time = (start + end) / 2
    if diarization is None:
        return "Unknown"
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if turn.start <= mid_time <= turn.end:
            return speaker
    return "Unknown"

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        if "video" not in request.files:
            error = "No file part in the request."
            return render_template("index.html", error=error)
        file = request.files["video"]
        if file.filename == "":
            error = "No file selected."
            return render_template("index.html", error=error)

        # STEP 1: Save the uploaded video to a temporary file.
        filename = file.filename
        video_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{filename}")
        file.save(video_filename)

        # STEP 2: Extract audio from the video.
        audio_filename = os.path.splitext(video_filename)[0] + ".wav"
        ffmpeg_command = [
            "ffmpeg",
            "-y",                # overwrite if exists
            "-i", video_filename,
            "-ac", "1",          # mono
            "-ar", "16000",      # 16 kHz sample rate
            audio_filename
        ]
        try:
            subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            error = "Error processing the video file. Please ensure it is a valid video."
            os.remove(video_filename)
            return render_template("index.html", error=error)

        # STEP 3: Run speaker diarization.
        HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

        if not HUGGINGFACE_TOKEN:
            raise ValueError("Hugging Face token not found!")

        diarization = None
        try:
            from pyannote.audio import Pipeline
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization",
                use_auth_token=HUGGINGFACE_TOKEN
            )
            diarization = diarization_pipeline(audio_filename)
        except Exception as e:
            print("Speaker diarization failed:", e)
            diarization = None

        # STEP 4: Transcribe audio with Whisper.
        result = model.transcribe(audio_filename)
        transcript_text = result.get("text", "")
        segments = result.get("segments", [])

        # STEP 5: Build the WebVTT file.
        # We'll generate placeholder labels for each unique speaker.
        vtt_lines = ["WEBVTT", ""]
        placeholder_map = {}  # Maps original speaker value to placeholder (e.g. "Unknown" -> "SPEAKER_01")
        counter = 1
        for segment in segments:
            start_ts = format_timestamp(segment["start"])
            end_ts = format_timestamp(segment["end"])
            text = segment["text"].strip()
            orig_speaker = get_speaker_for_segment(diarization, segment["start"], segment["end"])
            # Assign a placeholder if not already done.
            if orig_speaker not in placeholder_map:
                placeholder_map[orig_speaker] = f"SPEAKER_{counter:02d}"
                counter += 1
            placeholder = placeholder_map[orig_speaker]
            vtt_lines.append(f"{start_ts} --> {end_ts}")
            vtt_lines.append(f"[{placeholder}] {text}")
            vtt_lines.append("")  # blank line between cues

        vtt_content = "\n".join(vtt_lines)

        # STEP 6: Cleanup the extracted audio.
        os.remove(audio_filename)
        # Note: We intentionally keep the video file (video_filename) for preview.

        # Generate a unique id for this job and store results.
        uid = str(uuid.uuid4())
        generated_files[uid] = {
            "vtt": vtt_content,
            "transcript": transcript_text,
            "video_path": video_filename,
            "placeholder_map": placeholder_map  # original->placeholder mapping
        }
        # Prepare a sorted list of placeholders for the edit page.
        # Sort by the numeric part of the placeholder label.
        placeholders = sorted(placeholder_map.values(), key=lambda x: int(x.split('_')[1]))
        return render_template("edit.html", uid=uid, placeholders=placeholders)
    return render_template("index.html", error=error)

@app.route("/video/<uid>")
def video(uid):
    # Serve the uploaded video file for preview.
    if uid not in generated_files or "video_path" not in generated_files[uid]:
        return "Video not found", 404
    return send_file(generated_files[uid]["video_path"])

@app.route("/download/<uid>")
def download(uid):
    file_type = request.args.get("type")
    if uid not in generated_files or file_type not in generated_files[uid]:
        return "Requested file not found.", 404
    content = generated_files[uid][file_type]
    if file_type == "vtt":
        filename = "subtitles.vtt"
        mimetype = "text/vtt"
    elif file_type == "transcript":
        filename = "transcript.txt"
        mimetype = "text/plain"
    else:
        filename = "file.txt"
        mimetype = "text/plain"
    return send_file(
        io.BytesIO(content.encode("utf-8")),
        download_name=filename,
        mimetype=mimetype,
        as_attachment=True
    )

@app.route("/update_speakers/<uid>", methods=["POST"])
def update_speakers(uid):
    if uid not in generated_files:
        return "Job not found", 404
    # The form will contain keys corresponding to each placeholder (e.g., SPEAKER_01, SPEAKER_02, etc.)
    # Build a mapping from placeholder to new speaker name.
    new_mapping = {}
    for key, value in request.form.items():
        # If the user leaves the field blank, keep the original placeholder.
        new_mapping[key] = value.strip() if value.strip() != "" else key

    # Update the VTT content by replacing all occurrences of each placeholder with the new name.
    updated_vtt = generated_files[uid]["vtt"]
    for placeholder, new_name in new_mapping.items():
        # Replace the placeholder inside square brackets.
        updated_vtt = updated_vtt.replace(f"[{placeholder}]", f"[{new_name}]")
    # Save the updated vtt.
    generated_files[uid]["vtt"] = updated_vtt

    return render_template("final.html", uid=uid)

if __name__ == "__main__":
    app.run(debug=True)
