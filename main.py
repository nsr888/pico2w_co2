import asyncio
import gc
import utime
import os
import time
import sys

import network
import ujson
from machine import I2C, SPI, Pin

import sdcard
from ds3231 import DS3231
from microdot import Microdot, send_file
from scd4x import SCD4X
from utemplate.source import Loader
from ssd1306 import SSD1306_I2C

_stats = {
    "requests_total": 0,
    "uptime": time.time(),
}
# I2C setup
i2c = I2C(0, scl=Pin(5), sda=Pin(4))
print("I2C devices found:", i2c.scan())
scd = SCD4X(i2c)
rtc = DS3231(i2c)

# OLED display setup
display = SSD1306_I2C(128, 32, i2c)
display.poweron()
display.fill(0)
display.show()

# Set default time to DS3231 on startup
if False:  # Set to True to enable setting time
    rtc.datetime((2025, 8, 12, 21, 12))
    dt = rtc.datetime()
    print(
        f"Timestamp: {dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"
    )
    sys.exit()

# SPI setup for SD card
spi = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
cs = Pin(13)
sd = sdcard.SDCard(spi, cs)
os.mount(sd, "/sd")

# Initialize SCD40
scd.start_periodic_measurement()


asyncio.sleep(10)  # Give time for I2C and SPI to initialize

# WiFi connection
station = network.WLAN(network.STA_IF)
station.active(True)
station.config(pm=0xA11140)

# Read SSID from password_work.txt file
try:
    with open("password_work.txt", "r") as f:
        lines = f.readlines()
        if len(lines) >= 2:
            SSID = lines[0].strip()
            PASSWORD = lines[1].strip()
        else:
            print(
                "Error: password_work.txt must contain SSID on first line and password on second line"
            )
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
ip_address = station.ifconfig()[0]
print("IP address:", ip_address)

# Global variables for CO2 readings
current_co2 = None
last_measurement_time = None

# Global variable for tracking last weekly log write time
last_weekly_log_time = None

app = Microdot()

# Initialize template loader
template_loader = Loader(None, "templates")


def get_timestamp():
    dt = rtc.datetime()
    return f"{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d} {dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"


def get_week_number(year, month, day):
    """
    Calculate ISO week number for a given date.
    Compatible with MicroPython.
    """
    t = utime.mktime((year, month, day, 0, 0, 0, 0, 0))

    # utime.localtime(t) returns a tuple: (year, month, mday, hour, minute, second, weekday, yearday)
    # weekday is 0 for Monday, 6 for Sunday.
    # yearday is 1-366
    date_tuple = utime.localtime(t)
    year, month, day, _, _, _, weekday, yearday = date_tuple

    # ISO 8601 weekday is 1 for Monday, 7 for Sunday
    iso_weekday = weekday + 1

    # The core ISO week number algorithm
    # See: https://en.wikipedia.org/wiki/ISO_week_date#Calculating_the_week_number_from_an_ordinal_date
    week_number = (yearday - iso_weekday + 10) // 7

    if week_number < 1:
        # This date belongs to the last week of the previous year
        return get_week_number(year - 1, 12, 31)
    if (
        week_number == 53
        and utime.localtime(utime.mktime((year, 12, 31, 0, 0, 0, 0, 0)))[6] < 3
    ):
        # If Dec 31st is a Mon, Tue, or Wed, then it's week 1 of the next year
        return 1

    return week_number


def get_weekly_log_filename():
    """Generate weekly log filename with week number"""
    dt = rtc.datetime()
    year, month, day = dt[0], dt[1], dt[2]
    week_number = get_week_number(year, month, day)
    return f"/sd/readings/week{week_number}.csv"


def should_log_weekly():
    """Check if we should write to weekly log (hourly granularity)"""
    global last_weekly_log_time

    if last_weekly_log_time is None:
        return True

    dt = rtc.datetime()
    current_time = (dt[0], dt[1], dt[2], dt[4])  # year, month, day, hour

    # Parse last log time
    try:
        last_parts = last_weekly_log_time.split(" ")[0].split(
            "-"
        ) + last_weekly_log_time.split(" ")[1].split(":")
        last_time = (
            int(last_parts[0]),
            int(last_parts[1]),
            int(last_parts[2]),
            int(last_parts[3]),
        )  # year, month, day, hour

        # Check if at least one hour has passed
        if (
            current_time[0] > last_time[0]
            or current_time[1] > last_time[1]  # different year
            or current_time[2] > last_time[2]  # different month
            or current_time[3] != last_time[3]  # different day
        ):  # different hour
            return True
    except:
        # If parsing fails, assume we should log
        return True

    return False


def ensure_weekly_log_file():
    """Ensure weekly log file exists with header"""
    # Create readings directory if it doesn't exist
    try:
        os.mkdir("/sd/readings")
    except OSError as e:
        if e.errno != 17:  # 17 is EEXIST (directory already exists)
            raise

    filename = get_weekly_log_filename()
    try:
        with open(filename, "r") as f:
            pass
    except OSError:
        with open(filename, "w") as f:
            f.write("time,co2\n")
    return filename


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


def update_display(co2_value, ip_address):
    """Update OLED display with CO2 reading and IP address"""
    display.fill(0)

    # Display CO2 value in large text
    if co2_value is not None:
        co2_text = f"CO2: {co2_value}"
    else:
        co2_text = "CO2: --"

    # CO2 text uses the full width, centered at the top
    display.text(co2_text, 0, 0)

    # Display IP address in small font at bottom
    if ip_address:
        ip_text = ip_address
        display.text(ip_text, 0, 20)

    display.show()


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
                if file.startswith("week") and file.endswith(".csv"):
                    stat = os.stat(f"/sd/readings/{file}")
                    size = stat[6]
                    log_files.append((file, size))
            except UnicodeError:
                # Skip files with encoding issues
                continue
    except OSError:
        pass

    log_files.sort(reverse=True)  # Show newest first

    # Render template
    template = template_loader.load("index.tpl")
    html = "".join(
        template(
            current_co2=current_co2,
            last_measurement_time=last_measurement_time or "",
            current_time=get_timestamp(),
            log_files=log_files,
        )
    )

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

    # For weekly files, show the filename without extension
    pretty_date = filename[:-4]  # Remove .csv extension

    # Render template
    template = template_loader.load("chart.tpl")
    html = "".join(
        template(
            title=pretty_date,
            json_data=json_data,
            is_weekly=True,
        )
    )

    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/truncate/<filename>")
async def truncate_csv(request, filename):
    """Remove last line from a CSV file"""
    # Security: validate filename is in readings directory only
    if not filename.startswith("week") or not filename.endswith(".csv"):
        return (
            {"success": False, "error": "Invalid filename"},
            400,
            {"Content-Type": "application/json"},
        )

    result = remove_last_line_from_csv(filename)
    return result, 200, {"Content-Type": "application/json"}


@app.route("/status")
async def status(request):
    return get_system_info(), 200, {"Content-Type": "application/json"}


def remove_last_line_from_csv(filename):
    """Remove exactly one line from the end of a CSV file, preserving header"""
    full_path = f"/sd/readings/{filename}"

    try:
        # Read all lines
        with open(full_path, "r") as f:
            lines = f.readlines()

        # Check if we have data beyond header
        if len(lines) <= 1:
            return {"success": False, "error": "No data lines to remove"}

        # Remove last data line (keep header)
        del lines[-1]

        # Write back file
        with open(full_path, "w") as f:
            f.write("".join(lines))

        return {"success": True, "lines_removed": 1, "file": filename}

    except OSError:
        return {"success": False, "error": "File not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


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

        # Log to weekly file with hourly granularity
        if should_log_weekly():
            weekly_filename = ensure_weekly_log_file()
            with open(weekly_filename, "a") as f:
                f.write(f"{ts},{co2}\n")
            # Update last weekly log time
            global last_weekly_log_time
            last_weekly_log_time = ts

        # Update last measurement time
        global last_measurement_time
        last_measurement_time = ts

        # Update display with latest CO2 reading and IP
        update_display(current_co2, ip_address)

        print("System info:", get_system_info())
        await asyncio.sleep(60 * 5)  # Update every 5 minute


async def main():
    # Show IP address on display once connected
    update_display("----", ip_address)

    # Start web server and CO2 monitor concurrently
    await asyncio.gather(start_web_server(), co2_monitor_loop())


# Run the main async loop
asyncio.run(main())
