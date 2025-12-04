# IP Logger

A simple Logger with advanced device fingerprinting capabilities using Cloudflare Tunnels.

## Features

- **Automatic Tunnel Creation** - Generates public HTTPS links via Cloudflare without port forwarding
- **Advanced Fingerprinting** - Collects Canvas, Audio, and WebGL fingerprints
- **Geolocation Tracking** - ISP, organization, coordinates, and timezone detection
- **WebRTC Leak Detection** - Identifies local IP addresses behind VPNs
- **Security Analysis** - Detects proxies, VPNs, and hosting providers
- **JSON Export** - Automatically saves all logs on exit

## Requirements

- Python 3.7+
- Internet connection
- Windows, Linux, or macOS

## Installation

```bash
# Clone the repository
git clone https://github.com/Ghost0Dev/simple-IPlogger.git
cd simple-IPlogger

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Start

Simply run the batch file (Windows) or execute the Python script directly:

```bash
# Windows
start.bat

# Linux/macOS
python main.py
```

The script will automatically:
1. Download and configure Cloudflare Tunnel
2. Generate a public HTTPS link
3. Start monitoring incoming connections

### Accessing Logs

Press `Ctrl+C` to stop the server. (All captured stuff will be automatically saved to a JSON file) .

### Network Information
- IPv4/IPv6 addresses
- ISP and organization details
- AS (Autonomous System) number

### Geolocation
- Country, region, and city
- Postal code
- GPS coordinates
- Timezone

### Device Fingerprint
- Screen resolution
- GPU renderer
- CPU thread count
- Platform and language settings
- Unique canvas and audio signatures

## Configuration

Edit `main.py` to customize:

```python
PORT = 5000                          # Local server port
REDIRECT_URL = "https://www.google.com"  # Post-log redirect destination
```

## Project Structure

```
simple-IPlogger/
├── main.py              # Core application
├── requirements.txt     # Python dependencies
├── start.bat           # Windows launcher
└── README.md           # Documentation
```

## Legal Disclaimer

This tool is **ONLY** for **educational and diagnostic purposes only**. 

I am **NOT** responsible for misuse of this software.

