import asyncio
import gc
import os
import time

import network
import ujson
import urequests
from machine import I2C, SPI, Pin

import sdcard
from ds3231 import DS3231
from microdot import Microdot, send_file
from scd4x import SCD4X

_stats = {
    "requests_total": 0,
    "uptime": time.time(),
}
# I2C setup
i2c = I2C(0, scl=Pin(5), sda=Pin(4))
print("I2C devices found:", i2c.scan())
scd = SCD4X(i2c)
rtc = DS3231(i2c)

# Set default time to DS3231 on startup
if False:  # Set to True to enable setting time
    rtc.datetime((2025, 7, 20, 12, 43))

# SPI setup for SD card
spi = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
cs = Pin(13)
sd = sdcard.SDCard(spi, cs)
os.mount(sd, "/sd")

# Initialize SCD40
scd.start_periodic_measurement()


# Ensure readings directory exists and CSV file exists with header
def get_current_log_filename():
    """Generate filename with current datetime suffix"""
    dt = rtc.datetime()
    return f"/sd/readings/readings_{dt[0]:04d}{dt[1]:02d}{dt[2]:02d}.csv"


def ensure_log_file():
    """Ensure readings directory exists and current hour's log file exists with header"""
    # Create readings directory if it doesn't exist
    try:
        os.mkdir("/sd/readings")
    except OSError as e:
        if e.errno != 17:  # 17 is EEXIST (directory already exists)
            raise

    filename = get_current_log_filename()
    try:
        with open(filename, "r") as f:
            pass
    except OSError:
        with open(filename, "w") as f:
            f.write("time,co2\n")
    return filename


asyncio.sleep(10)  # Give time for I2C and SPI to initialize

# WiFi connection
station = network.WLAN(network.STA_IF)
station.active(True)
station.config(pm=0xA11140)

# Read SSID from password_work.txt file
try:
    with open("password_home.txt", "r") as f:
        lines = f.readlines()
        if len(lines) >= 2:
            SSID = lines[0].strip()
            PASSWORD = lines[1].strip()
        else:
            print("Error: password_work.txt must contain SSID on first line and password on second line")
            raise SystemExit
except OSError as e:
    print(f"Error reading password_work.txt: {e}")
    raise SystemExit

station.connect(SSID, PASSWORD)

for _ in range(20):
    if (
        station.isconnected()
        and station.status() == network.STAT_GOT_IP
        and station.ifconfig()[0] != "0.0.0.0"
    ):
        break
    time.sleep(1)

print("Wi-Fi connected:", station.isconnected())
print("IP address:", station.ifconfig())

# Global variables for CO2 readings
current_co2 = None
last_measurement_time = None

# Global variables for PM2.5 pollution data
current_pm25 = None
last_pm25_fetch_time = None

app = Microdot()


def get_timestamp():
    dt = rtc.datetime()
    return f"{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"


def fetch_pm25_data():
    """Fetch PM2.5 data from OpenAQ API"""
    global current_pm25, last_pm25_fetch_time

    try:
        url = "https://api.openaq.org/v3/sensors/3646910"
        headers = {
            "X-API-Key": "cd813fb1d25c3b7e82abb94bb7992e68ad55e8208b8a1041b4834f9fac4b9f5d"
        }

        response = urequests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data.get("results") and len(data["results"]) > 0:
                latest = data["results"][0].get("latest")
                if latest:
                    current_pm25 = round(latest["value"])
                    last_pm25_fetch_time = latest["datetime"]["local"]
                    print(
                        f"PM2.5 updated: {current_pm25} µg/m³ at {last_pm25_fetch_time}"
                    )
                    return True

        response.close()

    except Exception as e:
        print(f"Error fetching PM2.5 data: {e}")

    return False


def list_files(directory):
    """List all files in a directory"""
    try:
        return [
            f
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]
    except OSError:
        return []


@app.route("/")
async def index(request):
    log_files = []
    try:
        # Get directory listing with error handling
        try:
            files = os.listdir("/sd/readings")
        except UnicodeError:
            files = []  # Handle UnicodeError at directory level

        for file in files:
            try:
                if file.startswith("readings_") and file.endswith(".csv"):
                    stat = os.stat(f"/sd/readings/{file}")
                    size = stat[6]
                    log_files.append((file, size))
            except UnicodeError:
                # Skip files with encoding issues
                continue
    except OSError:
        pass

    log_files.sort(reverse=True)  # Show newest first

    html = "<html><head><title>CO2 Monitor</title></head><body>"
    html += "<h1>CO2 Monitor</h1>"
    if current_co2 is not None:
        html += f"<p>Current CO2 level: <strong><meter id='tempMeter' value='{current_co2}' min='400' max='1500'>{current_co2}</meter> {current_co2} ppm</strong></p>"
        html += "<ul>"
        html += f"<li>Current time: {get_timestamp()}</li>"
        html += f"<li>Last updated: {last_measurement_time}</li>"
        html += "<li>CO2 sensor: <a href='https://sensirion.com/products/catalog/SCD40'>SCD40</a></li>"
        html += "<li>Values greater than 1000 ppm are considered unhealthy.</li>"
        html += "</ul>"
    else:
        html += "<p>Waiting for first reading...</p>"

    # Add PM2.5 pollution data
    if current_pm25 is not None:
        html += f"<p>Current PM2.5: <strong><meter id='tempMeter' value='{current_pm25}' min='0' max='100'>{current_pm25}</meter> {current_pm25} &micro;g/m&sup3;</strong></p>"
        html += "<ul>"
        html += f"<li>PM2.5 last updated: {last_pm25_fetch_time}</li>"
        html += "<li>PM2.5 data source: <a href='https://explore.openaq.org/locations/663499'>OpenAQ</a></li>"
        html += "<li>PM2.5 data is updated every hour.</li>"
        html += "<li>Values greater than 35 &micro;g/m&sup3; are considered unhealthy.</li>"
        html += "</ul>"
    else:
        html += "<p>PM2.5 data: Waiting for first reading...</p>"
    html += "<p><a href='/co2'>JSON API</a></p>"
    html += "<h2>Log Files</h2>"
    html += "<table border='1' cellpadding='5'>"
    html += "<tr><th>Filename</th><th>Size</th><th>Actions</th></tr>"

    for filename, size in log_files:
        html += "<tr>"
        html += f"<td>{filename}</td>"
        html += f"<td>{size} bytes</td>"
        html += "<td>"
        html += f"<a href='/download/{filename}'>Download</a> | "
        html += f"<a href='/delete/{filename}' onclick=\"return confirm('Are you sure?')\">Delete</a> | "
        html += f"<a href='/spark/{filename}'>Sparkline</a>"
        html += "</td>"
        html += "</tr>"

    html += "</table>"
    html += "</body></html>"

    return html, 200, {"Content-Type": "text/html"}


@app.route("/co2")
async def co2_api(request):
    if current_co2 is not None:
        return (
            {"co2": current_co2, "timestamp": last_measurement_time},
            200,
            {"Content-Type": "application/json"},
        )
    else:
        return (
            {"co2": None, "status": "Data not ready"},
            200,
            {"Content-Type": "application/json"},
        )


@app.route("/delete/<filename>")
async def delete_file(request, filename):
    try:
        os.remove(f"/sd/readings/{filename}")
        return "redirect", 302, {"Location": "/"}
    except OSError:
        return "File not found", 404


@app.route("/download/<filename>")
async def download_file(request, filename):
    try:
        filestream = open(f"/sd/readings/{filename}", "rb")
        return send_file(
            f"/sd/readings/{filename}", file_extension="csv", stream=filestream
        )
    except OSError as e:
        return f"File {filename} not found: {e}", 404


@app.route("/spark/<filename>")
async def spark(request, filename):
    path = f"/sd/readings/{filename}"
    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except OSError:
        return "File not found", 404

    data = []
    for ln in lines[1:]:
        ln = ln.strip()
        if not ln:
            continue
        t, c = ln.split(",")
        data.append([t, int(c)])

    json_data = ujson.dumps(data)
    date_part = filename[9:17]
    pretty_date = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"

    html = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>CO2 {pretty_date}</title>
    <style>
      body{{margin:0;background:#fafafa;font-family:sans-serif}}
      svg{{display:block;margin:20px auto;background:#fff;border:1px solid #ddd}}
      polyline{{fill:none;stroke:#4caf50;stroke-width:2}}
      text{{font-size:12px;fill:#333}}
    </style>
  </head>
  <body>
    <svg id="spark" width="1000" height="600"></svg>
    <script>
      (function(){{
        const data = {json_data};
        const svg = document.getElementById("spark");
        const W = +svg.getAttribute("width"), H = +svg.getAttribute("height");
        const marginX=60, marginY=40, innerW=W-2*marginX, innerH=H-2*marginY;

        // Fixed CO2 reference lines
        const co2Levels = [500, 1000, 1500, 2000];
        const maxValue = 2000;
        const minValue = 0;

        // Create 24-hour x-axis
        const hourLabels = [];
        for (let i = 0; i < 24; i++) {{
          const x = marginX + (i * innerW / 23);
          const txt = document.createElementNS(svg.namespaceURI,"text");
          txt.setAttribute("x", x);
          txt.setAttribute("y", H-15);
          txt.setAttribute("text-anchor", "middle");
          txt.textContent = `${{i.toString().padStart(2, '0')}}:00`;
          hourLabels.push(txt);
        }}

        // Add horizontal reference lines for CO2 levels
        const refLines = [];
        co2Levels.forEach(level => {{
          const y = marginY + innerH - ((level - minValue) / (maxValue - minValue)) * innerH;
          const line = document.createElementNS(svg.namespaceURI, "line");
          line.setAttribute("x1", marginX);
          line.setAttribute("y1", y);
          line.setAttribute("x2", marginX + innerW);
          line.setAttribute("y2", y);
          line.setAttribute("stroke", "#ccc");
          line.setAttribute("stroke-width", 1);
          line.setAttribute("stroke-dasharray", "3,3");
          refLines.push(line);

          // Add labels for reference lines
          const label = document.createElementNS(svg.namespaceURI, "text");
          label.setAttribute("x", marginX + innerW + 5);
          label.setAttribute("y", y + 4);
          label.setAttribute("fill", "#666");
          label.textContent = `${{level}}ppm`;
          refLines.push(label);
        }});

        // Map measurements to timeline positions
        const vals = data.map(d => d[1]);
        const pts = data.map(d => {{
          const [datePart, timePart] = d[0].split(' ');
          const [hour, minute, second] = timePart.split(':').map(Number);
          const timeIndex = hour + minute/60 + second/3600;
          const x = marginX + (timeIndex * innerW / 24);
          const y = marginY + innerH - ((d[1] - minValue) / (maxValue - minValue)) * innerH;
          return `${{x}},${{y}}`;
        }}).join(" ");

        svg.innerHTML = `<g>
          ${{refLines.map(line => line.outerHTML).join('')}}
          <polyline points="${{pts}}" stroke="#4caf50" stroke-width="2" fill="none"/>
        </g>`;

        const title = document.createElementNS(svg.namespaceURI,"text");
        title.setAttribute("x", W/2);
        title.setAttribute("y", 25);
        title.setAttribute("text-anchor", "middle");
        title.textContent = `CO₂ concentration (ppm) - {pretty_date}`;
        svg.appendChild(title);

        // Add hour labels
        hourLabels.forEach(label => svg.appendChild(label));
      }})();
    </script>
  </body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/status")
async def status(request):
    return get_system_info(), 200, {"Content-Type": "application/json"}


def get_system_info():
    gc.collect()
    free = gc.mem_free()
    total = gc.mem_free() + gc.mem_alloc()
    uptime = time.time() - _stats["uptime"]
    return {
        "mem_free": free,
        "mem_used": total - free,
        "mem_total": total,
        "uptime": int(uptime),
        "requests_total": _stats["requests_total"],
    }


async def start_web_server():
    print("Starting web server on port 80...")
    await app.start_server(host="0.0.0.0", port=80, debug=True)


async def co2_monitor_loop(max_retries: int = 10):
    global current_co2
    global co2_led
    print("Starting CO2 monitor loop...")
    while True:
        ts = get_timestamp()
        print(f"Timestamp: {ts}")

        for _ in range(max_retries):
            if scd.data_ready:
                break  # success
            await asyncio.sleep(1)

        co2 = scd.co2
        current_co2 = co2  # Update global variable
        print(f"CO2: {co2} ppm")

        # Log to SD card in hourly rotated file
        log_filename = ensure_log_file()
        with open(log_filename, "a") as f:
            f.write(f"{ts},{co2}\n")

        # Update last measurement time
        global last_measurement_time
        last_measurement_time = ts

        print("System info:", get_system_info())
        await asyncio.sleep(60 * 5)  # Update every 5 minute


async def pm25_monitor_loop():
    """Fetch PM2.5 data from OpenAQ API once per hour"""
    print("Starting PM2.5 monitor loop...")

    # Fetch initial data
    fetch_pm25_data()

    while True:
        await asyncio.sleep(60 * 60)  # Wait 1 hour
        fetch_pm25_data()


async def main():
    # Start web server, CO2 monitor, and PM2.5 monitor concurrently
    await asyncio.gather(start_web_server(), co2_monitor_loop(), pm25_monitor_loop())


# Run the main async loop
asyncio.run(main())
