from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp as youtube_dl
import os

app = Flask(__name__)

# Ensure the downloads directory exists
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# Function to download video as mp3


def download_as_mp3(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            mp3_filename = filename.rsplit(
                '.', 1)[0] + '.mp3'  # Rename to mp3 format
            if os.path.exists(filename):
                os.rename(filename, mp3_filename)
            return mp3_filename
    except Exception as e:
        return f"Error: {str(e)}"

# Function to download video as mp4


def download_as_mp4(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            return filename
    except Exception as e:
        return f"Error: {str(e)}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    option = request.form['option']

    if option == 'mp3':
        filename_or_error = download_as_mp3(url)
        if "Error" in filename_or_error:
            return jsonify({'status': 'error', 'message': filename_or_error})
        # Send the filename to trigger download
        return jsonify({'status': 'success', 'message': filename_or_error})

    elif option == 'mp4':
        filename_or_error = download_as_mp4(url)
        if "Error" in filename_or_error:
            return jsonify({'status': 'error', 'message': filename_or_error})
        # Send the filename to trigger download
        return jsonify({'status': 'success', 'message': filename_or_error})

    return jsonify({'status': 'error', 'message': 'Invalid option'})


@app.route('/download_file', methods=['GET'])
def send_converted_file():
    file_path = request.args.get('file')
    if file_path:
        response = send_file(file_path, as_attachment=True)
        os.remove(file_path)  # Delete the file after sending it
        return response
    return jsonify({'status': 'error', 'message': 'File path not provided'})


if __name__ == '__main__':
    app.run(debug=True)
