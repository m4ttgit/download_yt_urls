# YouTube Channel Video List Downloader

## Description
A Python application with a simple graphical interface to extract all video titles and URLs from a YouTube channel and save them as a CSV file. It supports various YouTube channel URL formats and organizes the output neatly in a dedicated folder.

## Features
- Supports multiple YouTube channel URL formats (`@username`, `/c/channelname`, `/user/username`, `/channel/id`)
- Folder selection dialog for easy output directory choice
- Saves video titles and URLs in CSV format
- Robust error handling with informative messages
- Lightweight, user-friendly Gradio interface
- Does **not** download videos, only fetches metadata

## Requirements
- **Python 3.x**
- **yt-dlp** installed and accessible in your system's PATH
- Python packages:
  - `gradio`

## Installation

1. **Install Python 3.x**  
   [Download Python](https://www.python.org/downloads/)

2. **Install yt-dlp**  
   You can install via pip:  
   ```
   pip install -U yt-dlp
   ```  
   Or download the standalone binary from [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp#installation)

3. **Install required Python packages**  
   ```
   pip install gradio
   ```

## Usage

1. Run the application:  
   ```
   python app.py
   ```

2. In the GUI:
   - Enter the YouTube channel URL (e.g., `https://www.youtube.com/@channelname`)
   - Select or type the output directory path
   - Click **"Get Video List"**

3. The app will:
   - Extract all video titles and URLs from the channel
   - Save them into a CSV file named `<channel_name>_video_list.csv`
   - Place the CSV inside a subfolder named after the channel within your selected directory

## Output

- The CSV file contains two columns:
  - `title`: The video title
  - `url`: The direct YouTube video URL

- Example CSV filename:  
  ```
  mychannel/mychannel_video_list.csv
  ```

## Notes
- The tool **does not download videos**, only fetches metadata.
- Ensure `yt-dlp` is installed and accessible in your system's PATH.
- If you encounter errors, check the console output or error messages in the app.
- Existing example output files:
  - `video_list.txt`
  - `mikee-ai/mikee-ai_video_list.csv`

## License
TODO: Add license information here.
