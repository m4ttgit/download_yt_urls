import gradio as gr
import subprocess
import csv
import os
import re
import tkinter as tk
from tkinter import filedialog
import sys

def extract_channel_name(url):
    """Extracts a usable channel name from various YouTube URL formats."""
    # Try common patterns first
    patterns = [
        r"youtube\.com/(@[\w.-]+)",      # @username format
        r"youtube\.com/c/([\w.-]+)",       # /c/channelname format
        r"youtube\.com/user/([\w.-]+)",    # /user/username format
        r"youtube\.com/channel/([\w.-]+)" # /channel/id format
    ]
    channel_name = None
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            channel_name = match.group(1)
            break

    # Fallback: try the last part of the path if it seems reasonable
    if not channel_name:
        try:
            path_parts = url.strip('/').split('/')
            # Check if the last part looks like a potential name (avoiding query params etc.)
            last_part = path_parts[-1]
            if last_part and not bool(re.search(r'[=&?]', last_part)) and len(last_part) > 2:
                 # Basic check: not empty, no common query chars, length > 2
                 channel_name = last_part
        except Exception:
            pass # Ignore errors during fallback parsing

    # Sanitize the extracted name for filesystem use
    if channel_name:
        # Remove leading '@' if present
        if channel_name.startswith('@'):
            channel_name = channel_name[1:]
        # Replace invalid filesystem characters with underscores
        channel_name = re.sub(r'[<>:"/\\|?*]+', '_', channel_name)
        # Replace consecutive underscores/spaces with a single underscore
        channel_name = re.sub(r'[_ ]+', '_', channel_name).strip('_')
        return channel_name
    else:
        return None

def get_videos_and_save(channel_url, output_dir):
    """Fetches video titles and URLs and saves them to a CSV file."""
    if not channel_url or not output_dir:
        return "Error: Please provide both Channel URL and Output Directory."

    # Basic URL validation
    if not re.match(r"https?://(www\.)?youtube\.com/", channel_url, re.IGNORECASE):
         return f"Error: Invalid YouTube URL format. Must start with http(s)://youtube.com/"

    channel_name = extract_channel_name(channel_url)
    if not channel_name:
        return f"Error: Could not extract a usable channel name from the URL: {channel_url}"

    # Construct save path
    save_folder = os.path.join(output_dir, channel_name)
    csv_filepath = os.path.join(save_folder, f'{channel_name}_video_list.csv')

    try:
        os.makedirs(save_folder, exist_ok=True)
        print(f"Ensured directory exists: {save_folder}") # Debug print
    except OSError as e:
        return f"Error creating directory '{save_folder}': {e}"
    except Exception as e:
         return f"Error during directory creation setup '{save_folder}': {e}"

    # Construct yt-dlp command
    # Using semicolon as delimiter because titles might contain commas
    # Adding --ignore-errors and --flat-playlist
    # Note: --flat-playlist might conflict with --print '%(title)s...'
    # If titles are missing in the output, remove --flat-playlist
    command = [
        'yt-dlp',
        '--ignore-errors',
        '--skip-download',
        '--flat-playlist', # Attempting to add for speed, may break title extraction
        '--print', '%(title)s;%(webpage_url)s',
        channel_url
    ]
    print(f"Executing command: {' '.join(command)}") # Debug print

    try:
        # Execute command
        # Use shell=True on Windows if yt-dlp path issues occur, but list is safer
        # Set creationflags on Windows to hide console window
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE # Hide console window

        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', startupinfo=startupinfo)

        # Check stderr for potential yt-dlp specific errors even if return code is 0 (due to --ignore-errors)
        if result.returncode != 0:
             print(f"Warning: yt-dlp exited with code {result.returncode}") # Log warning
             print(f"yt-dlp stderr: {result.stderr}") # Log stderr

        if not result.stdout and result.stderr:
             # If stdout is empty but stderr has content, report stderr
             return f"Error: yt-dlp failed.\nstderr: {result.stderr}"
        elif not result.stdout:
             return f"Error: yt-dlp produced no output. Check channel URL and yt-dlp installation. Stderr: {result.stderr}"


        output_lines = result.stdout.strip().split('\n')
        print(f"Received {len(output_lines)} lines from yt-dlp.") # Debug print

        # Prepare data for CSV
        video_data = []
        for i, line in enumerate(output_lines):
            line = line.strip() # Clean whitespace
            if not line: # Skip empty lines
                continue
            if ';' in line:
                # Split only on the last semicolon to handle titles with semicolons
                parts = line.rsplit(';', 1)
                if len(parts) == 2:
                    title, url = parts[0].strip(), parts[1].strip()
                    # Basic check if url looks like a youtube url
                    if url.startswith("https://www.youtube.com/watch?v="):
                         video_data.append({'title': title, 'url': url})
                    else:
                         print(f"Warning: Skipping line {i+1} - Parsed URL doesn't look like a YouTube video URL: {url} (Original line: {line})")
                else:
                    # Handle lines that don't split correctly
                    print(f"Warning: Skipping malformed line {i+1} (unexpected split result): {line}")
            else:
                 # This might catch error messages printed by yt-dlp to stdout
                 print(f"Warning: Skipping line {i+1} without expected delimiter ';': {line}")

        if not video_data:
             # Check stderr again if no valid data was parsed
             stderr_info = f"\nstderr: {result.stderr}" if result.stderr else ""
             return f"Warning: No valid video data extracted. yt-dlp output might be empty or in an unexpected format.{stderr_info}"

        print(f"Processed {len(video_data)} valid video entries.") # Debug print

        # Write to CSV
        try:
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['title', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(video_data)
            print(f"Successfully wrote data to {csv_filepath}") # Debug print
            return f"Success! {len(video_data)} videos saved to: {csv_filepath}"
        except IOError as e:
            return f"Error writing to CSV file '{csv_filepath}': {e}"
        except Exception as e:
            return f"An unexpected error occurred during CSV writing: {e}"

    except FileNotFoundError:
        return "Error: 'yt-dlp' command not found. Make sure yt-dlp is installed and in your system's PATH."
    except subprocess.CalledProcessError as e:
        # This might not be hit often with check=False, but good practice
        return f"Error executing yt-dlp: {e}\nstderr: {e.stderr}"
    except Exception as e:
        # Catch other potential errors during subprocess execution
        import traceback
        print(f"Unexpected error during subprocess execution: {traceback.format_exc()}") # Log full traceback
        return f"An unexpected error occurred during processing: {e}"

# Function to open folder dialog using tkinter
def select_folder():
    """Opens a dialog to select a folder and returns the path."""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main tkinter window
        root.attributes('-topmost', True) # Bring the dialog to the front
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        root.destroy()
        if folder_path: # Return path only if user selected one
            return folder_path
        else:
            # Return gr.update() to keep the existing value if canceled
            return gr.update()
    except Exception as e:
        print(f"Error opening folder dialog: {e}")
        # Return gr.update() to avoid clearing the textbox on error
        return gr.update()


# --- Gradio Interface ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# YouTube Channel Video List Downloader")
    gr.Markdown(
        "Enter a YouTube channel URL (e.g., `https://www.youtube.com/@channelname`, `https://www.youtube.com/c/channelname`, or `https://www.youtube.com/user/username`)\n"
        "and select an output directory. The tool will fetch all video titles and URLs from the channel page\n"
        "and save them to a CSV file inside a new subfolder (named after the channel) within your selected directory."
    )

    with gr.Row():
        channel_input = gr.Textbox(
            label="YouTube Channel URL",
            placeholder="e.g., https://www.youtube.com/@datasciencecentral"
        )

    with gr.Row():
        output_dir_input = gr.Textbox(
            label="Output Directory Path",
            placeholder="Select or type the path where the channel folder should be created",
            interactive=True # Allow typing path manually too
        )
        browse_button = gr.Button("📁 Browse Folder")

    with gr.Row():
        submit_button = gr.Button("🚀 Get Video List", variant="primary")

    output_message = gr.Textbox(label="Result", interactive=False) # Read-only output

    # --- Event Handlers ---
    browse_button.click(
        fn=select_folder,
        inputs=None,            # No input needed for the folder dialog function
        outputs=output_dir_input # Update the output directory textbox with the selected path
    )

    submit_button.click(
        fn=get_videos_and_save,
        inputs=[channel_input, output_dir_input],
        outputs=output_message
    )

if __name__ == "__main__":
    # Recommended: Add share=False unless you intend to share publicly
    demo.launch(share=False)
