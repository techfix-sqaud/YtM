from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp as youtube_dl
import os
import re
import mimetypes
import urllib.parse
from werkzeug.utils import secure_filename
import uuid
import time
import threading
from datetime import datetime, timedelta

app = Flask(__name__)

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Helpers


def sanitize_filename(name):
    """Sanitize filename by removing problematic characters and limiting length"""
    # First decode any URL encoding that might be present
    name = urllib.parse.unquote(name)

    # Remove problematic characters for filesystem
    sanitized = re.sub(r'[\\/*?:"<>|]', '', name)
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()
    # Remove or replace other problematic characters
    sanitized = sanitized.replace('&', 'and')
    sanitized = re.sub(r'[^\w\s\-_\.]', '', sanitized)
    # Limit length to avoid filesystem issues
    if len(sanitized) > 100:
        # Keep the extension intact
        name_part, ext = os.path.splitext(sanitized)
        max_name_length = 100 - len(ext)
        sanitized = name_part[:max_name_length] + ext
    # Ensure we have a valid filename
    if not sanitized or sanitized == '.':
        sanitized = 'download'
    return sanitized


def allowed_extension(ext):
    return ext.lower() in ['.mp3', '.mp4']


def get_mime_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

# Download logic


def get_file_size_mb(file_path):
    """Get file size in MB"""
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)
    return 0


def download_youtube(url, format_choice):
    """Download YouTube video/audio with simplified, mobile-friendly approach"""

    # Generate unique filename to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())

    # Simple filename template
    if format_choice == 'mp3':
        filename_template = f"audio_{timestamp}_{unique_id}.%(ext)s"
    else:
        filename_template = f"video_{timestamp}_{unique_id}.%(ext)s"

    output_path = os.path.join(DOWNLOAD_DIR, filename_template)

    # Simplified options for better compatibility
    base_options = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_path,
        'ignoreerrors': False,
        'extractaudio': format_choice == 'mp3',
        'audioformat': 'mp3' if format_choice == 'mp3' else None,
    }

    if format_choice == 'mp3':
        base_options.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        })
    elif format_choice == 'mp4':
        base_options.update({
            'format': 'best[height<=720][ext=mp4]/best[height<=720]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })
    else:
        return None, "Invalid format choice"

    try:
        with youtube_dl.YoutubeDL(base_options) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=False)
            duration = info.get('duration', 0)
            title = info.get('title', 'download')

            # Check duration limits
            if format_choice == 'mp4' and duration and duration > 5400:  # 90 minutes like ytmp3.cc
                return None, "Video is too long (max 90 minutes)"

            # Download the file
            ydl.download([url])

            # Find the downloaded file
            target_ext = 'mp3' if format_choice == 'mp3' else 'mp4'

            # Look for files that match our pattern
            for filename in os.listdir(DOWNLOAD_DIR):
                if filename.startswith(f"{'audio' if format_choice == 'mp3' else 'video'}_{timestamp}_{unique_id}"):
                    file_path = os.path.join(DOWNLOAD_DIR, filename)
                    if os.path.exists(file_path):
                        # Check file size
                        file_size_mb = get_file_size_mb(file_path)
                        max_size = 16 if format_choice == 'mp4' else 100

                        if file_size_mb > max_size:
                            os.remove(file_path)  # Clean up large file
                            return None, f"File too large ({file_size_mb:.1f}MB). Max: {max_size}MB for {format_choice.upper()}"

                        # Rename to clean filename
                        clean_title = sanitize_filename(
                            title)[:50]  # Limit length
                        final_filename = f"{clean_title}.{target_ext}"
                        final_path = os.path.join(DOWNLOAD_DIR, final_filename)

                        # Handle duplicate filenames
                        counter = 1
                        while os.path.exists(final_path):
                            name_part = f"{clean_title}_{counter}"
                            final_filename = f"{name_part}.{target_ext}"
                            final_path = os.path.join(
                                DOWNLOAD_DIR, final_filename)
                            counter += 1

                        os.rename(file_path, final_path)
                        return final_path, None

            return None, "Download failed - no output file found"

    except Exception as e:
        return None, f"Download error: {str(e)}"


def cleanup_old_files():
    """Remove files older than 1 hour to prevent disk space issues"""
    try:
        if not os.path.exists(DOWNLOAD_DIR):
            return

        current_time = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > 3600:  # 1 hour in seconds
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up old file: {filename}")
                    except OSError:
                        pass
    except Exception as e:
        print(f"Error during cleanup: {e}")


def start_cleanup_timer():
    """Start periodic cleanup every 30 minutes"""
    cleanup_old_files()
    threading.Timer(1800, start_cleanup_timer).start()  # 30 minutes


# Start cleanup timer when app starts
start_cleanup_timer()

# URL Validation


def is_valid_youtube_url(url):
    """Check if URL is a valid YouTube URL"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=',
        r'(?:https?://)?(?:www\.)?youtu\.be/',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/',
        r'(?:https?://)?m\.youtube\.com/watch\?v=',
    ]

    for pattern in youtube_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False

# Routes


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    option = request.form.get('option')

    if not url or not option:
        return jsonify({'status': 'error', 'message': 'Missing URL or option'})

    # Validate YouTube URL
    if not is_valid_youtube_url(url):
        return jsonify({'status': 'error', 'message': 'Invalid YouTube URL'})

    file_path, error = download_youtube(url, option)
    if error:
        return jsonify({'status': 'error', 'message': error})

    filename = os.path.basename(file_path)
    return jsonify({'status': 'success', 'filename': filename})


@app.route('/download_file')
def download_file():
    """Simplified file download endpoint optimized for mobile"""
    filename = request.args.get('file')
    if not filename:
        return jsonify({'status': 'error', 'message': 'No file specified'}), 400

    # Construct file path
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    # Check if file exists
    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

    # Determine MIME type based on extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext == '.mp3':
        mime_type = 'audio/mpeg'
    elif file_ext == '.mp4':
        mime_type = 'video/mp4'
    else:
        mime_type = 'application/octet-stream'

    try:
        # Create response with proper headers for mobile compatibility
        response = send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )

        # Set headers for better mobile and cross-browser compatibility
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = mime_type
        response.headers['Content-Length'] = str(os.path.getsize(file_path))
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        # Mobile-specific headers
        user_agent = request.headers.get('User-Agent', '').lower()
        if any(device in user_agent for device in ['android', 'iphone', 'ipad', 'mobile']):
            response.headers['Content-Transfer-Encoding'] = 'binary'
            response.headers['X-Content-Type-Options'] = 'nosniff'

        return response

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Download failed: {str(e)}'}), 500


@app.route('/file_info')
def file_info():
    """Get information about a downloaded file"""
    filename = request.args.get('file')
    if not filename:
        return jsonify({'status': 'error', 'message': 'No file specified'}), 400

    file_path = os.path.join(DOWNLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        file_ext = os.path.splitext(filename)[1].lower()

        return jsonify({
            'status': 'success',
            'filename': filename,
            'size_bytes': file_size,
            'size_mb': round(file_size_mb, 2),
            'extension': file_ext,
            'whatsapp_compatible': file_size_mb <= (16 if file_ext == '.mp4' else 100)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to get file info: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
