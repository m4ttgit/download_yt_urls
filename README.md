# YouTube Channel Video List Downloader

## Overview
A web tool to extract all video titles and URLs from a YouTube channel and save them as a CSV file. Includes a Gradio interface and a web UI with BuyMeACoffee support.

## Features
- Extracts all video URLs and titles from a YouTube channel.
- Saves results as a CSV file.
- Simple web interface built with Flask.
- Gradio interface for local use.
- Disclaimer included.
- BuyMeACoffee button for donations.

## Installation

1. **Clone the repository**

```bash
git clone https://your-repo-url.git
cd your-repo-directory
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Ensure `yt-dlp` is installed**

- The project uses the `yt-dlp` Python package.
- You may also want to install the standalone binary for better performance:

```bash
pip install yt-dlp
```

or download from [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp).

## Usage

### Run the Flask web app

```bash
python server.py
```

or

```bash
python app.py
```

- Open your browser and go to `http://localhost:5000`.

### Gradio interface

```bash
python app.py
```

- Gradio UI will launch in your browser.

## Disclaimer
This tool is not affiliated with YouTube or Google. It is the user's responsibility to ensure that they have the right to download content. Downloading copyrighted material without permission may violate YouTube's Terms of Service and applicable laws. This service is intended for personal and fair-use purposes only.
