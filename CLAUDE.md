# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a MicroPython-based CO2 monitoring system for Raspberry Pi Pico W that:
- Reads CO2 data from an SCD40 sensor via I2C
- Logs data to CSV files on SD card with daily rotation and weekly aggregation
- Serves a web dashboard with real-time CO2 readings and data visualization
- Provides SVG-based charts for daily (5-minute intervals) and weekly (hourly intervals) data
- Includes a development HTML generator for testing templates with fake data

## Key Commands

### MicroPython Device Operations
- `make run` - Run main.py on connected MicroPython device
- `make push` - Copy main.py to device
- `make push_all` - Copy all files to device (including templates and utemplate)
- `make pull_main` - Copy main.py from device to local
- `make ls` - List files on device

### HTML Development and Testing
- `make generate-html` - Generate all HTML files with fake data scenarios
- `make preview-dashboard` - Generate and open dashboard (excellent conditions)
- `make preview-daily` - Generate and open daily chart
- `make preview-weekly` - Generate and open weekly chart  
- `make clean-html` - Remove generated HTML files
- `python3 generate_html.py all` - Generate all test scenarios
- `python3 generate_html.py dashboard --scenario excellent --open` - Generate specific scenario

## Architecture

### Template System
The project uses **utemplate** - a lightweight templating engine that compiles templates to Python functions:
- **Source templates**: `templates/*.tpl` - Human-readable template files with `{% %}` syntax
- **Compiled templates**: `templates/*_tpl.py` - Auto-generated Python render functions
- **CRITICAL**: Both source and compiled files must be updated when making template changes, as MicroPython uses the compiled versions

### Air Quality State System
CO2 readings are categorized into exactly 3 states:
- **Excellent 👍** (≤ 1000 ppm) - scenario: "excellent" 
- **Increase Ventilation 💨** (1000-1500 ppm) - scenario: "ventilation"
- **Action Required 🚨** (> 1500 ppm) - scenario: "action"

### Data Logging Pattern
- **Daily logs**: `/sd/readings/readings_YYYYMMDD.csv` - 5-minute interval measurements
- **Weekly logs**: `/sd/readings/week{N}.csv` - Hourly aggregated measurements using ISO week numbers
- CSV format: `time,co2` with timestamp format `YYYY-MM-DD HH:MM:SS`

### Chart Visualization
- **Daily charts**: 24-hour timeline, measurements every 5 minutes, x-axis shows hours (00:00-23:00)
- **Weekly charts**: 7-day timeline, measurements every hour, x-axis shows dates, precise boundaries (00:01 first day to 23:01 last day)
- **SVG rendering**: Client-side JavaScript with fixed CO2 reference lines (500, 1000, 1500, 2000 ppm)

### Hardware Interfaces
- **SCD40 sensor**: I2C on pins SCL=5, SDA=4 for CO2/temperature/humidity
- **DS3231 RTC**: I2C for accurate timekeeping
- **SD card**: SPI on pins SCK=10, MOSI=11, MISO=12, CS=13 for data storage
- **WiFi credentials**: Read from `password_work.txt` (SSID on line 1, password on line 2)

### Web Server Routes
- `/` - Main dashboard with current CO2, file listing, and controls
- `/co2` - JSON API for current reading
- `/spark/<filename>` - SVG chart generation from CSV data
- `/download/<filename>` - File download
- `/delete/<filename>` - File deletion
- `/status` - System information (memory, uptime, request count)

## Development Patterns

### Template Development Workflow
1. Edit source template in `templates/*.tpl`
2. Update corresponding compiled template in `templates/*_tpl.py` 
3. Test with `make generate-html` using fake data generator
4. Deploy to device with `make push_all`

### Testing with Fake Data
The `generate_html.py` script creates realistic test scenarios:
- **Timing precision**: Daily charts use midnight-to-midnight, weekly charts use precise 00:01-23:01 boundaries
- **Measurement intervals**: Daily every 5 minutes, weekly every hour
- **Test scenarios**: Complete data, partial data (first 2 days), gaps (missing 2 middle days)
- **Air quality scenarios**: All three CO2 states with realistic values

### Data Generation Timing Rules
- Daily data: Single day from 00:00:00 to 23:55:00 in 5-minute intervals
- Weekly data: 7 days from 00:01:00 (first day) to 23:01:00 (last day) in hourly intervals  
- Weekly data includes fixed 1500 ppm values at first/last measurements for visual debugging
- All timestamps follow format: `YYYY-MM-DD HH:MM:SS`

### Chart Positioning Logic
- **Daily**: x-position = `(hour + minute/60) * chartWidth / 24`
- **Weekly**: x-position = `(dayIndex + timeFraction) * chartWidth / numDays` where timeFraction accounts for hour/minute within day
- **Y-axis**: Linear scale from 0-2000 ppm with reference lines at key thresholds