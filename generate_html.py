#!/usr/bin/env python3
"""
HTML Generator for CO2 Monitor Templates with Fake Data
Generates static HTML files using utemplate with realistic fake data
"""
import argparse
import json
import os
import random
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '.')
from utemplate.source import Loader


class FakeDataGenerator:
    """Generate realistic fake data for CO2 monitor templates"""
    
    def __init__(self, base_date=None):
        self.base_date = base_date or datetime.now()
        random.seed(42)  # Consistent fake data for reproducibility
    
    def get_timestamp(self, offset_hours=0, offset_minutes=0):
        """Generate timestamp in the format used by the CO2 monitor"""
        dt = self.base_date + timedelta(hours=offset_hours, minutes=offset_minutes)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_co2_reading(self, base_value=450, variation=50):
        """Generate realistic CO2 reading with some variation"""
        return random.randint(max(400, base_value - variation), base_value + variation)
    
    
    def generate_log_files(self):
        """Generate realistic log file entries"""
        files = []
        
        # Generate daily files for the last week
        for i in range(7):
            date = self.base_date - timedelta(days=i)
            filename = f"readings_{date.strftime('%Y%m%d')}.csv"
            size = random.randint(1024, 8192)
            files.append((filename, size))
        
        # Generate weekly files
        for week in [32, 31, 30]:
            filename = f"week{week}.csv"
            size = random.randint(10240, 51200)
            files.append((filename, size))
        
        return files
    
    def generate_daily_chart_data(self):
        """Generate 24 hours of CO2 data for daily chart"""
        data = []
        base_co2 = 450
        
        # Start from midnight of the current day
        start_of_day = self.base_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for hour in range(24):
            for minute_offset in range(0, 60, 5):  # Every 5 minutes
                # Simulate daily CO2 pattern: lower at night, higher during day
                time_factor = 1.0
                if 6 <= hour <= 22:  # Daytime - higher CO2
                    time_factor = 1.2 + 0.3 * random.random()
                else:  # Nighttime - lower CO2
                    time_factor = 0.8 + 0.2 * random.random()
                
                co2_value = int(base_co2 * time_factor + random.randint(-30, 30))
                co2_value = max(400, min(2000, co2_value))  # Clamp to realistic range
                
                # Generate timestamp from midnight of current day
                timestamp_dt = start_of_day + timedelta(hours=hour, minutes=minute_offset)
                timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
                data.append([timestamp, co2_value])
        
        return data
    
    def generate_weekly_chart_data(self):
        """Generate week of CO2 data for weekly chart"""
        data = []
        base_co2 = 480
        
        # Start from 7 days ago at 00:01, end at 23:01 of current day
        start_of_week = self.base_date - timedelta(days=6)
        start_of_week = start_of_week.replace(hour=0, minute=1, second=0, microsecond=0)
        
        for day in range(7):
            for hour in range(24):  # Every hour
                # Weekly variation: weekends might be different
                day_factor = 1.0
                if day in [5, 6]:  # Weekend
                    day_factor = 0.9
                
                co2_value = int(base_co2 * day_factor + random.randint(-40, 40))
                co2_value = max(400, min(2000, co2_value))
                
                # Generate timestamp: all measurements at :01 of each hour
                # First measurement: 00:01, last measurement: 23:01 of last day
                timestamp_dt = start_of_week + timedelta(days=day, hours=hour)
                
                timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
                data.append([timestamp, co2_value])
        
        # Override first and last measurements with fixed 1500 value for debugging
        if data:
            data[0][1] = 1500  # First measurement
            data[-1][1] = 1500  # Last measurement
        
        return data
    
    def generate_weekly_chart_data_partial_first2days(self):
        """Generate weekly chart data with measurements only for first 2 days"""
        data = []
        base_co2 = 480
        
        # Start from 7 days ago at 00:01
        start_of_week = self.base_date - timedelta(days=6)
        start_of_week = start_of_week.replace(hour=0, minute=1, second=0, microsecond=0)
        
        for day in range(2):  # Only first 2 days
            for hour in range(24):  # Every hour
                # Weekly variation: weekends might be different
                day_factor = 1.0
                if day in [5, 6]:  # Weekend
                    day_factor = 0.9
                
                co2_value = int(base_co2 * day_factor + random.randint(-40, 40))
                co2_value = max(400, min(2000, co2_value))
                
                # Generate timestamp: all measurements at :01 of each hour
                timestamp_dt = start_of_week + timedelta(days=day, hours=hour)
                timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
                data.append([timestamp, co2_value])
        
        # Override first and last measurements with fixed 1500 value for debugging
        if data:
            data[0][1] = 1500  # First measurement
            data[-1][1] = 1500  # Last measurement
        
        return data
    
    def generate_weekly_chart_data_with_gap(self):
        """Generate weekly chart data with gap (missing measurements for 2 days in middle)"""
        data = []
        base_co2 = 480
        
        # Start from 7 days ago at 00:01
        start_of_week = self.base_date - timedelta(days=6)
        start_of_week = start_of_week.replace(hour=0, minute=1, second=0, microsecond=0)
        
        for day in range(7):
            # Skip days 2 and 3 (create a 2-day gap in the middle)
            if day in [2, 3]:
                continue
                
            for hour in range(24):  # Every hour
                # Weekly variation: weekends might be different
                day_factor = 1.0
                if day in [5, 6]:  # Weekend
                    day_factor = 0.9
                
                co2_value = int(base_co2 * day_factor + random.randint(-40, 40))
                co2_value = max(400, min(2000, co2_value))
                
                # Generate timestamp: all measurements at :01 of each hour
                timestamp_dt = start_of_week + timedelta(days=day, hours=hour)
                timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
                data.append([timestamp, co2_value])
        
        # Override first and last measurements with fixed 1500 value for debugging
        if data:
            data[0][1] = 1500  # First measurement
            data[-1][1] = 1500  # Last measurement
        
        return data


class HTMLGenerator:
    """Generate HTML files from templates using fake data"""
    
    def __init__(self, output_dir="html_preview"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.loader = Loader(None, "templates")
        self.fake_data = FakeDataGenerator()
    
    def generate_dashboard(self, scenario="excellent"):
        """Generate main dashboard HTML"""
        print("Generating dashboard HTML...")
        
        # Configure data based on scenario
        if scenario == "excellent":
            current_co2 = self.fake_data.generate_co2_reading(420, 20)
        elif scenario == "ventilation":
            current_co2 = self.fake_data.generate_co2_reading(1300, 100)
        elif scenario == "action":
            current_co2 = self.fake_data.generate_co2_reading(1700, 200)
        else:
            current_co2 = self.fake_data.generate_co2_reading()
        
        # Generate template data
        template_data = {
            'current_co2': current_co2,
            'last_measurement_time': self.fake_data.get_timestamp(offset_minutes=-5),
            'current_time': self.fake_data.get_timestamp(),
            'log_files': self.fake_data.generate_log_files()
        }
        
        # Render template
        template = self.loader.load("index.tpl")
        html = "".join(template(**template_data))
        
        # Write file
        filename = f"dashboard_{scenario}.html"
        output_file = self.output_dir / filename
        output_file.write_text(html, encoding='utf-8')
        
        print(f"✓ Generated {output_file}")
        return output_file
    
    def generate_daily_chart(self):
        """Generate daily chart HTML"""
        print("Generating daily chart HTML...")
        
        chart_data = self.fake_data.generate_daily_chart_data()
        json_data = json.dumps(chart_data)
        
        template_data = {
            'title': f"Daily Chart - {self.fake_data.base_date.strftime('%Y-%m-%d')}",
            'json_data': json_data,
            'is_weekly': False
        }
        
        # Render template
        template = self.loader.load("chart.tpl")
        html = "".join(template(**template_data))
        
        # Write file
        output_file = self.output_dir / "daily_chart.html"
        output_file.write_text(html, encoding='utf-8')
        
        print(f"✓ Generated {output_file}")
        return output_file
    
    def generate_weekly_chart(self):
        """Generate weekly chart HTML"""
        print("Generating weekly chart HTML...")
        
        chart_data = self.fake_data.generate_weekly_chart_data()
        json_data = json.dumps(chart_data)
        
        template_data = {
            'title': f"Weekly Chart - Week {self.fake_data.base_date.isocalendar()[1]}",
            'json_data': json_data,
            'is_weekly': True
        }
        
        # Render template
        template = self.loader.load("chart.tpl")
        html = "".join(template(**template_data))
        
        # Write file
        output_file = self.output_dir / "weekly_chart.html"
        output_file.write_text(html, encoding='utf-8')
        
        print(f"✓ Generated {output_file}")
        return output_file
    
    def generate_weekly_chart_partial(self):
        """Generate weekly chart HTML with partial data (first 2 days only)"""
        print("Generating weekly chart with partial data (first 2 days only)...")
        
        chart_data = self.fake_data.generate_weekly_chart_data_partial_first2days()
        json_data = json.dumps(chart_data)
        
        template_data = {
            'title': f"Weekly Chart (Partial) - Week {self.fake_data.base_date.isocalendar()[1]}",
            'json_data': json_data,
            'is_weekly': True
        }
        
        # Render template
        template = self.loader.load("chart.tpl")
        html = "".join(template(**template_data))
        
        # Write file
        output_file = self.output_dir / "weekly_chart_partial.html"
        output_file.write_text(html, encoding='utf-8')
        
        print(f"✓ Generated {output_file}")
        return output_file
    
    def generate_weekly_chart_gap(self):
        """Generate weekly chart HTML with gap (missing 2 days in middle)"""
        print("Generating weekly chart with gap (missing 2 days in middle)...")
        
        chart_data = self.fake_data.generate_weekly_chart_data_with_gap()
        json_data = json.dumps(chart_data)
        
        template_data = {
            'title': f"Weekly Chart (Gap) - Week {self.fake_data.base_date.isocalendar()[1]}",
            'json_data': json_data,
            'is_weekly': True
        }
        
        # Render template
        template = self.loader.load("chart.tpl")
        html = "".join(template(**template_data))
        
        # Write file
        output_file = self.output_dir / "weekly_chart_gap.html"
        output_file.write_text(html, encoding='utf-8')
        
        print(f"✓ Generated {output_file}")
        return output_file
    
    def generate_all(self):
        """Generate all HTML files"""
        print(f"Generating all HTML files to {self.output_dir}/")
        
        files = []
        
        # Generate different dashboard scenarios
        for scenario in ["excellent", "ventilation", "action"]:
            files.append(self.generate_dashboard(scenario))
        
        # Generate charts
        files.append(self.generate_daily_chart())
        files.append(self.generate_weekly_chart())
        files.append(self.generate_weekly_chart_partial())
        files.append(self.generate_weekly_chart_gap())
        
        # Create index file listing all generated files
        self._create_index_file(files)
        
        return files
    
    def _create_index_file(self, generated_files):
        """Create an index.html file listing all generated files"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>CO2 Monitor - Template Preview</title>
    <style>
        body {{ font-family: sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4caf50; padding-bottom: 10px; }}
        .file-grid {{ display: grid; gap: 20px; margin-top: 30px; }}
        .file-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 20px; background: #fafafa; }}
        .file-card h3 {{ margin-top: 0; color: #4caf50; }}
        .file-card p {{ color: #666; margin: 10px 0; }}
        .file-card a {{ display: inline-block; background: #4caf50; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-top: 10px; }}
        .file-card a:hover {{ background: #45a049; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌱 CO2 Monitor Template Preview</h1>
        <p>Generated HTML files from utemplate with fake data scenarios</p>
        <p class="timestamp">Generated: {timestamp}</p>
        
        <div class="file-grid">
            <div class="file-card">
                <h3>📊 Dashboard Scenarios</h3>
                <p>Main dashboard with different air quality conditions</p>
                <a href="dashboard_excellent.html">👍 Excellent</a>
                <a href="dashboard_ventilation.html">💨 Increase Ventilation</a>
                <a href="dashboard_action.html">🚨 Action Required</a>
            </div>
            
            <div class="file-card">
                <h3>📈 Daily Chart</h3>
                <p>24-hour CO2 readings with realistic daily patterns</p>
                <a href="daily_chart.html">View Daily Chart</a>
            </div>
            
            <div class="file-card">
                <h3>📅 Weekly Charts</h3>
                <p>7-day CO2 trends showing week-long patterns</p>
                <a href="weekly_chart.html">Complete Week</a>
                <a href="weekly_chart_partial.html">Partial (2 days)</a>
                <a href="weekly_chart_gap.html">With Gap</a>
            </div>
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #e8f5e8; border-radius: 5px;">
            <h3>💡 About This Preview</h3>
            <p>These HTML files are generated from the same utemplate templates used in the MicroPython CO2 monitor. 
            The fake data simulates realistic sensor readings and system behavior for development and testing purposes.</p>
        </div>
    </div>
</body>
</html>"""
        
        index_file = self.output_dir / "index.html"
        index_file.write_text(html_content, encoding='utf-8')
        print(f"✓ Generated {index_file}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Generate HTML files from CO2 monitor templates with fake data")
    parser.add_argument(
        'command', 
        choices=['dashboard', 'daily', 'weekly', 'weekly-partial', 'weekly-gap', 'all'],
        help='What to generate'
    )
    parser.add_argument(
        '--scenario', 
        choices=['excellent', 'ventilation', 'action'], 
        default='excellent',
        help='Data scenario for dashboard (default: excellent)'
    )
    parser.add_argument(
        '--output', '-o', 
        default='html_preview',
        help='Output directory (default: html_preview)'
    )
    parser.add_argument(
        '--open', '-p', 
        action='store_true',
        help='Open generated file in browser'
    )
    
    args = parser.parse_args()
    
    generator = HTMLGenerator(args.output)
    
    if args.command == 'dashboard':
        output_file = generator.generate_dashboard(args.scenario)
    elif args.command == 'daily':
        output_file = generator.generate_daily_chart()
    elif args.command == 'weekly':
        output_file = generator.generate_weekly_chart()
    elif args.command == 'weekly-partial':
        output_file = generator.generate_weekly_chart_partial()
    elif args.command == 'weekly-gap':
        output_file = generator.generate_weekly_chart_gap()
    elif args.command == 'all':
        files = generator.generate_all()
        output_file = generator.output_dir / "index.html"
    
    print(f"\n🎉 HTML generation complete!")
    print(f"📁 Files saved to: {generator.output_dir}")
    
    if args.open:
        try:
            webbrowser.open(f"file://{output_file.absolute()}")
            print(f"🌐 Opened {output_file.name} in browser")
        except Exception as e:
            print(f"❌ Could not open browser: {e}")


if __name__ == "__main__":
    main()
