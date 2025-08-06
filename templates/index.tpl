{% args current_co2=None, last_measurement_time="", current_time="", log_files=[] %}
<!DOCTYPE html>
<html>
<head>
    <title>CO2 Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: sans-serif; 
            margin: 20px; 
            background: #f5f5f5;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px;
            border-radius: 5px;
        }
        h1 { 
            color: #333; 
            margin: 0 0 10px 0;
        }
        .co2-display {
            background: white;
            text-align: center;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #4caf50;
            border-radius: 5px;
        }
        .co2-display.warning {
            border-color: #f44336;
        }
        .co2-display.danger {
            border-color: #d32f2f;
            border-width: 3px;
        }
        .co2-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 5px 0;
        }
        .co2-value.warning {
            color: #f44336;
        }
        .co2-value.danger {
            color: #d32f2f;
        }
        .co2-status {
            font-size: 1.1em;
            margin: 5px 0;
        }
        meter {
            width: 200px;
            height: 20px;
        }
        .details {
            list-style: none;
            padding: 10px 0;
            margin: 0;
            font-size: 0.9em;
            color: #666;
        }
        .details li {
            margin: 3px 0;
        }
        a {
            color: #4caf50;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .api-link {
            display: inline-block;
            background: #4caf50;
            color: white;
            padding: 8px 16px;
            margin: 10px 0;
            border-radius: 3px;
        }
        .api-link:hover {
            background: #45a049;
            text-decoration: none;
        }
        h2 {
            color: #333;
            margin: 20px 0 10px 0;
            font-size: 1.2em;
        }
        .table-container {
            overflow-x: auto;
            margin: 10px 0;
        }
        table {
            width: 100%;
            min-width: 600px;
            border-collapse: collapse;
            background: white;
        }
        th {
            background: #4caf50;
            color: white;
            padding: 10px;
            text-align: left;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .actions a {
            display: inline-block;
            padding: 4px 8px;
            margin: 1px;
            font-size: 0.8em;
            border-radius: 3px;
            white-space: nowrap;
        }
        .download { background: #2196f3; color: white; }
        .delete { background: #f44336; color: white; }
        .chart { background: #9c27b0; color: white; }
        .waiting {
            text-align: center;
            padding: 20px;
            color: #666;
            font-style: italic;
        }
        @media (max-width: 600px) {
            body { margin: 10px; }
            .container { padding: 15px; }
            .co2-value { font-size: 2em; }
            meter { width: 150px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌱 CO2 Monitor</h1>
        
        {% if current_co2 is not None %}
        <div class="co2-display {% if current_co2 > 1500 %}danger{% elif current_co2 > 1000 %}warning{% endif %}">
            <div class="co2-value {% if current_co2 > 1500 %}danger{% elif current_co2 > 1000 %}warning{% endif %}">{{current_co2}} ppm</div>
            <div class="co2-status">
                {% if current_co2 > 1500 %}
                🚨 Action Required
                {% elif current_co2 > 1000 %}
                💨 Increase Ventilation
                {% else %}
                👍 Excellent
                {% endif %}
            </div>
            <meter value="{{current_co2}}" min="400" max="1500" optimum="450" high="800">{{current_co2}} ppm</meter>
            
            <ul class="details">
                <li>Updated: {{last_measurement_time}}</li>
                <li>Current time: {{current_time}}</li>
                <li>Sensor: <a href="https://sensirion.com/products/catalog/SCD40">SCD40</a></li>
            </ul>
        </div>
        {% else %}
        <div class="waiting">
            <div class="co2-value">⏳</div>
            <p>Waiting for first CO2 reading...</p>
        </div>
        {% endif %}

        <a href="/co2" class="api-link">JSON API</a>

        <h2>Data Files</h2>
        <div class="table-container">
            <table>
                <tr>
                    <th>Filename</th>
                    <th>Size</th>
                    <th>Actions</th>
                </tr>
                {% for filename, size in log_files %}
                <tr>
                    <td>{{filename}}</td>
                    <td>{{size}} bytes</td>
                    <td class="actions">
                        <a href="/download/{{filename}}" class="download">Download</a>
                        <a href="/delete/{{filename}}" class="delete" onclick="return confirm('Delete {{filename}}?')">Delete</a>
                        {% if filename.startswith("week") %}
                        <a href="/spark/{{filename}}" class="chart">Weekly Chart</a>
                        {% else %}
                        <a href="/spark/{{filename}}" class="chart">Daily Chart</a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        {% if not log_files %}
        <div class="waiting">
            <p>No data files available yet</p>
        </div>
        {% endif %}
    </div>
</body>
</html>