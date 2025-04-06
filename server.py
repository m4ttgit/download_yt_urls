import os
import re
import csv
import sys
import subprocess
import tempfile
from flask import Flask, request, jsonify, send_file, send_from_directory

app = Flask(__name__, static_folder='web_ui', static_url_path='')

def extract_channel_name(url):
    patterns = [
        r"youtube\.com/(@[\w.-]+)",
        r"youtube\.com/c/([\w.-]+)",
        r"youtube\.com/user/([\w.-]+)",
        r"youtube\.com/channel/([\w.-]+)"
    ]
    channel_name = None
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            channel_name = match.group(1)
            break

    if not channel_name:
        try:
            path_parts = url.strip('/').split('/')
            last_part = path_parts[-1]
            if last_part and not bool(re.search(r'[=&?]', last_part)) and len(last_part) > 2:
                channel_name = last_part
        except Exception:
            pass

    if channel_name:
        if channel_name.startswith('@'):
            channel_name = channel_name[1:]
        channel_name = re.sub(r'[<>:"/\\|?*]+', '_', channel_name)
        channel_name = re.sub(r'[_ ]+', '_', channel_name).strip('_')
        return channel_name
    else:
        return None

def get_videos_and_save(channel_url, output_dir, output_option):
    if not channel_url:
        return "Error: Please provide a Channel URL.", None

    if output_option == "save" and not output_dir:
        return "Error: Please provide an Output Directory.", None

    if not re.match(r"https?://(www\.)?youtube\.com/", channel_url, re.IGNORECASE):
        return "Error: Invalid YouTube URL format. Must start with http(s)://youtube.com/", None

    channel_name = extract_channel_name(channel_url)
    if not channel_name:
        return f"Error: Could not extract a usable channel name from the URL: {channel_url}", None

    if output_option == "save":
        save_folder = os.path.join(output_dir, channel_name)
    else:
        save_folder = tempfile.mkdtemp()

    csv_filepath = os.path.join(save_folder, f"{channel_name}_video_list.csv")

    try:
        os.makedirs(save_folder, exist_ok=True)
    except OSError as e:
        return f"Error creating directory '{save_folder}': {e}", None
    except Exception as e:
        return f"Error during directory creation setup '{save_folder}': {e}", None

    command = [
        'yt-dlp',
        '--ignore-errors',
        '--skip-download',
        '--flat-playlist',
        '--print', '%(title)s;%(webpage_url)s',
        channel_url
    ]

    try:
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', startupinfo=startupinfo)

        if result.returncode != 0:
            print(f"Warning: yt-dlp exited with code {result.returncode}")
            print(f"yt-dlp stderr: {result.stderr}")

        if not result.stdout and result.stderr:
            return f"Error: yt-dlp failed.\nstderr: {result.stderr}", None
        elif not result.stdout:
            return f"Error: yt-dlp produced no output. Check channel URL and yt-dlp installation. Stderr: {result.stderr}", None

        output_lines = result.stdout.strip().split('\n')

        video_data = []
        for line in output_lines:
            line = line.strip()
            if not line:
                continue
            if ';' in line:
                parts = line.rsplit(';', 1)
                if len(parts) == 2:
                    title, url = parts[0].strip(), parts[1].strip()
                    if url.startswith("https://www.youtube.com/watch?v="):
                        video_data.append({'title': title, 'url': url})

        if not video_data:
            stderr_info = f"\nstderr: {result.stderr}" if result.stderr else ""
            return f"Warning: No valid video data extracted. yt-dlp output might be empty or in an unexpected format.{stderr_info}", None

        try:
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['title', 'url'])
                writer.writeheader()
                writer.writerows(video_data)
        except IOError as e:
            return f"Error writing to CSV file '{csv_filepath}': {e}", None
        except Exception as e:
            return f"An unexpected error occurred during CSV writing: {e}", None

        if output_option == "save":
            return f"Success! {len(video_data)} videos saved to: {csv_filepath}", None
        else:
            return f"Success! {len(video_data)} videos processed.", csv_filepath

    except FileNotFoundError:
        return "Error: 'yt-dlp' command not found. Make sure yt-dlp is installed and in your system's PATH.", None
    except subprocess.CalledProcessError as e:
        return f"Error executing yt-dlp: {e}\nstderr: {e.stderr}", None
    except Exception as e:
        import traceback
        print(f"Unexpected error during subprocess execution: {traceback.format_exc()}")
        return f"An unexpected error occurred during processing: {e}", None

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    channel_url = data.get('channel_url')
    output_dir = data.get('output_dir')
    output_option = data.get('output_option', 'save')  # default to save

    message, csv_path = get_videos_and_save(channel_url, output_dir, output_option)

    if output_option == "download" and csv_path and os.path.exists(csv_path):
        try:
            return send_file(csv_path, as_attachment=True)
        except Exception as e:
            return jsonify({'message': f"Error sending file: {e}"})
    else:
        return jsonify({'message': message})

@app.route('/select_folder', methods=['GET'])
def select_folder():
    import tkinter as tk
    from tkinter import filedialog
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        root.destroy()
        if folder_path:
            return jsonify({'path': folder_path})
        else:
            return jsonify({'path': ''})
    except Exception as e:
        print(f"Error opening folder dialog: {e}")
        return jsonify({'path': ''})

from flask import send_file, request as flask_request

@app.route('/download_csv')
def download_csv():
    csv_path = flask_request.args.get('path')
    if not csv_path or not os.path.isfile(csv_path):
        return "File not found", 404
    try:
        return send_file(csv_path, as_attachment=True)
    except Exception as e:
        return f"Error sending file: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
