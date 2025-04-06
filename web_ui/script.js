document.getElementById('downloadBtn').addEventListener('click', async () => {
  const channelUrl = document.getElementById('channelUrl').value.trim();
  const outputDir = document.getElementById('outputDir').value.trim();
  const resultDiv = document.getElementById('result');
  const downloadLink = document.getElementById('downloadCsvBtn');

  // Hide download button initially
  downloadLink.style.display = 'none';
  downloadLink.href = '#';

  if (!channelUrl || !outputDir) {
    resultDiv.textContent = 'Please provide both the YouTube channel URL and output directory.';
    return;
  }

  resultDiv.textContent = 'Processing... Please wait.';
  try {
    const response = await fetch('/download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        channel_url: channelUrl,
        output_dir: outputDir
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      resultDiv.textContent = 'Server error: ' + errorText;
      return;
    }

    const data = await response.json();
    resultDiv.textContent = data.message || 'No response message received.';

    // Try to extract CSV path from message
    const match = data.message.match(/saved to:\s*(.*\.csv)/i);
    if (match && match[1]) {
      const csvPath = match[1].trim();
      downloadLink.href = `/download_csv?path=${encodeURIComponent(csvPath)}`;
      downloadLink.style.display = 'inline-block';
    }
  } catch (error) {
    console.error('Error:', error);
    resultDiv.textContent = 'Request failed: ' + error.message;
  }
});

document.getElementById('browseBtn').addEventListener('click', async () => {
  try {
    const response = await fetch('/select_folder');
    if (!response.ok) {
      console.error('Failed to open folder dialog');
      return;
    }
    const data = await response.json();
    if (data.path) {
      document.getElementById('outputDir').value = data.path;
    }
  } catch (error) {
    console.error('Error selecting folder:', error);
  }
});
