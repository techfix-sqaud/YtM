from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp as youtube_dl
import os
import re

app = Flask(__name__)

# Downloads directory (relative to this file)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def sanitize_filename(name):
    # Basic sanitization: remove problematic chars
    return re.sub(r'[\\/*?:"<>|]', '', name)


def download_as_mp3(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = sanitize_filename(info.get('title', 'download'))
            mp3_filename = os.path.join(DOWNLOAD_DIR, f"{title}.mp3")

            if not os.path.exists(mp3_filename):
                # Sometimes the extractor may output other formats first, rename if needed
                base_filename = os.path.join(DOWNLOAD_DIR, f"{title}")
                for ext in ['webm', 'm4a', 'wav']:
                    possible_file = f"{base_filename}.{ext}"
                    if os.path.exists(possible_file):
                        os.rename(possible_file, mp3_filename)
                        break
            if os.path.exists(mp3_filename):
                return mp3_filename
            else:
                return None
    except Exception as e:
        return f"Error: {str(e)}"


def download_as_mp4(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = sanitize_filename(info.get('title', 'download'))
            mp4_filename = os.path.join(DOWNLOAD_DIR, f"{title}.mp4")
            if os.path.exists(mp4_filename):
                return mp4_filename
            else:
                return None
    except Exception as e:
        return f"Error: {str(e)}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    option = request.form.get('option')

    if not url or not option:
        return jsonify({'status': 'error', 'message': 'Missing URL or option'})

    if option == 'mp3':
        file_path = download_as_mp3(url)
    elif option == 'mp4':
        file_path = download_as_mp4(url)
    else:
        return jsonify({'status': 'error', 'message': 'Invalid option'})

    if not file_path:
        return jsonify({'status': 'error', 'message': 'Failed to download or convert file.'})
    if isinstance(file_path, str) and file_path.startswith("Error"):
        return jsonify({'status': 'error', 'message': file_path})

    filename = os.path.basename(file_path)
    return jsonify({'status': 'success', 'filename': filename})


@app.route('/download_file')
def download_file():
    filename = request.args.get('file')
    if not filename:
        return jsonify({'status': 'error', 'message': 'No file specified'})

    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        return jsonify({'status': 'error', 'message': 'File not found'})

    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
