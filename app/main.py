from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp as youtube_dl
import os

app = Flask(__name__)

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# Download video as MP3
def download_as_mp3(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            base_filename = ydl.prepare_filename(info).rsplit('.', 1)[0]
            mp3_filename = base_filename + '.mp3'
            return os.path.basename(mp3_filename)  # return only filename
    except Exception as e:
        return f"Error: {str(e)}"


# Download video as MP4
def download_as_mp4(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4'
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return os.path.basename(filename)  # return only filename
    except Exception as e:
        return f"Error: {str(e)}"


# Homepage
@app.route('/')
def index():
    return render_template('index.html')


# Handle download request
@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    option = request.form.get('option')

    if not url or not option:
        return jsonify({'status': 'error', 'message': 'Missing URL or option'})

    if option == 'mp3':
        result = download_as_mp3(url)
    elif option == 'mp4':
        result = download_as_mp4(url)
    else:
        return jsonify({'status': 'error', 'message': 'Invalid option'})

    if result.startswith("Error"):
        return jsonify({'status': 'error', 'message': result})

    return jsonify({'status': 'success', 'filename': result})


# Serve the downloaded file
@app.route('/download_file', methods=['GET'])
def send_converted_file():
    filename = request.args.get('file')
    if not filename:
        return jsonify({'status': 'error', 'message': 'No file specified'})

    file_path = os.path.join(DOWNLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'File not found'})

    # Determine mimetype based on file extension
    mimetype = 'audio/mpeg' if filename.endswith('.mp3') else 'video/mp4'

    try:
        response = send_file(file_path, as_attachment=True, mimetype=mimetype)
        os.remove(file_path)  # Optional: cleanup after download
        return response
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# App entry point
if __name__ == '__main__':
    app.run(debug=True, port=5000)
