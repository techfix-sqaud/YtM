# from flask import Flask, render_template, request, send_file, jsonify
# import yt_dlp as youtube_dl
# import os
# import re

# app = Flask(__name__)

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
# os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# def sanitize_filename(name):
#     # Basic sanitization: remove problematic chars
#     return re.sub(r'[\\/*?:"<>|]', '', name)


# def download_as_mp3(url):
#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
#         'quiet': True,
#         'no_warnings': True,
#     }
#     try:
#         with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(url, download=True)
#             title = sanitize_filename(info.get('title', 'download'))
#             mp3_filename = os.path.join(DOWNLOAD_DIR, f"{title}.mp3")

#             if not os.path.exists(mp3_filename):
#                 # Sometimes the extractor may output other formats first, rename if needed
#                 base_filename = os.path.join(DOWNLOAD_DIR, f"{title}")
#                 for ext in ['webm', 'm4a', 'wav']:
#                     possible_file = f"{base_filename}.{ext}"
#                     if os.path.exists(possible_file):
#                         os.rename(possible_file, mp3_filename)
#                         break
#             if os.path.exists(mp3_filename):
#                 return mp3_filename
#             else:
#                 return None
#     except Exception as e:
#         return f"Error: {str(e)}"


# def download_as_mp4(url):
#     ydl_opts = {
#         'format': 'bestvideo+bestaudio/best',
#         'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
#         'merge_output_format': 'mp4',
#         'quiet': True,
#         'no_warnings': True,
#     }
#     try:
#         with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(url, download=True)
#             title = sanitize_filename(info.get('title', 'download'))
#             mp4_filename = os.path.join(DOWNLOAD_DIR, f"{title}.mp4")
#             if os.path.exists(mp4_filename):
#                 return mp4_filename
#             else:
#                 return None
#     except Exception as e:
#         return f"Error: {str(e)}"


# @app.route('/')
# def index():
#     return render_template('index.html')


# @app.route('/download', methods=['POST'])
# def download():
#     url = request.form.get('url')
#     option = request.form.get('option')

#     if not url or not option:
#         return jsonify({'status': 'error', 'message': 'Missing URL or option'})

#     if option == 'mp3':
#         file_path = download_as_mp3(url)
#     elif option == 'mp4':
#         file_path = download_as_mp4(url)
#     else:
#         return jsonify({'status': 'error', 'message': 'Invalid option'})

#     if not file_path:
#         return jsonify({'status': 'error', 'message': 'Failed to download or convert file.'})
#     if isinstance(file_path, str) and file_path.startswith("Error"):
#         return jsonify({'status': 'error', 'message': file_path})

#     filename = os.path.basename(file_path)
#     return jsonify({'status': 'success', 'filename': filename})


# @app.route('/download_file')
# def download_file():
#     filename = request.args.get('file')
#     if not filename:
#         return jsonify({'status': 'error', 'message': 'No file specified'})

#     file_path = os.path.join(DOWNLOAD_DIR, filename)
#     if not os.path.isfile(file_path):
#         return jsonify({'status': 'error', 'message': 'File not found'})

#     try:
#         return send_file(file_path, as_attachment=True)
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})


# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp as youtube_dl
import os
import re
import mimetypes
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Helpers


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)


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
    options = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'extractaudio': False,
        'audioformat': 'mp3',
        'ignoreerrors': True,
    }

    if format_choice == 'mp3':
        options.update({
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',  # Lower bitrate for WhatsApp compatibility
            }, {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }],
            'postprocessor_args': [
                '-ar', '44100',  # Standard sample rate
                '-ac', '2',      # Stereo
                '-b:a', '128k',  # Consistent bitrate
            ],
        })
    elif format_choice == 'mp4':
        options.update({
            'format': 'best[height<=720][ext=mp4]/best[height<=720]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }, {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }],
            'postprocessor_args': [
                '-c:v', 'libx264',           # H.264 codec for WhatsApp compatibility
                '-preset', 'medium',          # Balance between speed and compression
                '-crf', '23',                # Good quality compression
                '-c:a', 'aac',               # AAC audio codec
                '-b:a', '128k',              # Audio bitrate
                '-movflags', '+faststart',    # Enable fast start for web playback
                '-pix_fmt', 'yuv420p',       # Pixel format for compatibility
                '-maxrate', '1000k',         # Max bitrate to keep file size reasonable
                '-bufsize', '2000k',         # Buffer size
            ],
        })
    else:
        return None, "Invalid format choice"

    try:
        with youtube_dl.YoutubeDL(options) as ydl:
            # Extract info first to check duration and size estimates
            info = ydl.extract_info(url, download=False)
            duration = info.get('duration', 0)

            # Check if video is too long for WhatsApp (30 minutes limit)
            if format_choice == 'mp4' and duration > 1800:  # 30 minutes
                return None, "Video is too long for WhatsApp sharing (max 30 minutes)"

            # Now download
            info = ydl.extract_info(url, download=True)
            title = sanitize_filename(info.get('title', 'download'))
            ext = 'mp3' if format_choice == 'mp3' else 'mp4'
            final_path = os.path.join(DOWNLOAD_DIR, f"{title}.{ext}")

            # Handle edge cases where yt_dlp outputs another format
            if not os.path.exists(final_path):
                base = os.path.join(DOWNLOAD_DIR, title)
                for fallback_ext in ['webm', 'm4a', 'wav', 'mp4', 'mkv']:
                    alt_file = f"{base}.{fallback_ext}"
                    if os.path.exists(alt_file):
                        os.rename(alt_file, final_path)
                        break

            if os.path.exists(final_path):
                # Check file size for WhatsApp limits
                file_size_mb = get_file_size_mb(final_path)
                max_size = 16 if format_choice == 'mp4' else 100  # WhatsApp limits

                if file_size_mb > max_size:
                    return None, f"File too large ({file_size_mb:.1f}MB). WhatsApp limit: {max_size}MB for {format_choice.upper()}"

                return final_path, None
            else:
                return None, "File was not created."
    except Exception as e:
        return None, str(e)

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

    file_path, error = download_youtube(url, option)
    if error:
        return jsonify({'status': 'error', 'message': error})

    filename = os.path.basename(file_path)
    return jsonify({'status': 'success', 'filename': filename})


@app.route('/download_file')
def download_file():
    filename = request.args.get('file')
    if not filename:
        return jsonify({'status': 'error', 'message': 'No file specified'})

    safe_filename = secure_filename(filename)
    file_path = os.path.join(DOWNLOAD_DIR, safe_filename)

    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'File not found'})

    # Get file extension and set appropriate MIME type
    file_ext = os.path.splitext(safe_filename)[1].lower()

    if file_ext == '.mp3':
        mime_type = 'audio/mpeg'
    elif file_ext == '.mp4':
        mime_type = 'video/mp4'
    else:
        mime_type = 'application/octet-stream'

    try:
        # Get user agent to detect mobile browsers
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(device in user_agent for device in [
                        'android', 'iphone', 'ipad', 'mobile'])

        response = send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=safe_filename
        )

        # Set additional headers for better mobile compatibility
        response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        response.headers['Content-Type'] = mime_type
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        # For mobile browsers, set additional headers
        if is_mobile:
            response.headers['Content-Transfer-Encoding'] = 'binary'

        return response

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to send file: {e}'})


@app.route('/file_info')
def file_info():
    """Get information about a downloaded file"""
    filename = request.args.get('file')
    if not filename:
        return jsonify({'status': 'error', 'message': 'No file specified'})

    safe_filename = secure_filename(filename)
    file_path = os.path.join(DOWNLOAD_DIR, safe_filename)

    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'File not found'})

    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        file_ext = os.path.splitext(safe_filename)[1].lower()

        return jsonify({
            'status': 'success',
            'filename': safe_filename,
            'size_bytes': file_size,
            'size_mb': round(file_size_mb, 2),
            'extension': file_ext,
            'whatsapp_compatible': file_size_mb <= (16 if file_ext == '.mp4' else 100)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to get file info: {e}'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
