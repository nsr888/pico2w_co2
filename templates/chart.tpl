{% args title="CO2 Chart", json_data="[]", is_weekly=False %}
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>{{title}}</title>
    <style>
        body { margin: 0; background: #fafafa; font-family: sans-serif; }
        svg { display: block; margin: 20px auto; background: #fff; border: 1px solid #ddd; }
        polyline { fill: none; stroke: #4caf50; stroke-width: 2; }
        text { font-size: 12px; fill: #333; }
    </style>
</head>
<body>
    <svg id="spark" width="1000" height="600"></svg>
    <script>
        (function(){
            const data = {{json_data}};
            const svg = document.getElementById("spark");
            const W = +svg.getAttribute("width"), H = +svg.getAttribute("height");
            {% if is_weekly %}
            const marginX=80, marginY=40, innerW=W-2*marginX, innerH=H-2*marginY;
            {% else %}
            const marginX=60, marginY=40, innerW=W-2*marginX, innerH=H-2*marginY;
            {% endif %}

            // Fixed CO2 reference lines
            const co2Levels = [500, 1000, 1500, 2000];
            const maxValue = 2000;
            const minValue = 0;

            // Add horizontal reference lines for CO2 levels
            const refLines = [];
            co2Levels.forEach(level => {
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
                label.textContent = `${level}ppm`;
                refLines.push(label);
            });

            {% if is_weekly %}
            // Weekly chart logic
            const parseDate = (dateStr) => new Date(dateStr.split(' ')[0] + 'T00:00:00Z');
            const formatDate = (date) => date.toISOString().split('T')[0];

            const firstDate = parseDate(data[0][0]);
            const lastDate = parseDate(data[data.length - 1][0]);
            
            const fullDateRange = [];
            for (let d = new Date(firstDate); d <= lastDate; d.setDate(d.getDate() + 1)) {
                fullDateRange.push(formatDate(new Date(d)));
            }
            const numDays = fullDateRange.length;

            // Create x-axis labels for the full date range
            const dateLabels = [];
            fullDateRange.forEach((dateStr, i) => {
                const x = marginX + (i * innerW / (numDays - 1 || 1));
                const txt = document.createElementNS(svg.namespaceURI,"text");
                txt.setAttribute("x", x);
                txt.setAttribute("y", H-15);
                txt.setAttribute("text-anchor", "middle");
                txt.textContent = dateStr;
                dateLabels.push(txt);
            });

            // Map measurements to timeline positions using the full date range
            const pts = data.map(d => {
                const datePart = d[0].split(' ')[0];
                const dateIndex = fullDateRange.indexOf(datePart);
                if (dateIndex === -1) return ''; 
                
                const [hour, minute, second] = d[0].split(' ')[1].split(':').map(Number);
                const timeFraction = (hour * 3600 + minute * 60 + second) / 86400;
                
                const x = marginX + ((dateIndex + timeFraction) * innerW / numDays);
                const y = marginY + innerH - ((d[1] - minValue) / (maxValue - minValue)) * innerH;
                return `${x},${y}`;
            }).join(" ");

            svg.innerHTML = `<g>
                ${refLines.map(line => line.outerHTML).join('')}
                <polyline points="${pts}" stroke="#4caf50" stroke-width="2" fill="none"/>
            </g>`;

            const title = document.createElementNS(svg.namespaceURI,"text");
            title.setAttribute("x", W/2);
            title.setAttribute("y", 25);
            title.setAttribute("text-anchor", "middle");
            title.textContent = `CO₂ concentration (ppm) - {{title}}`;
            svg.appendChild(title);

            // Add date labels
            dateLabels.forEach(label => svg.appendChild(label));
            {% else %}
            // Daily chart logic
            const hourLabels = [];
            for (let i = 0; i < 24; i++) {
                const x = marginX + (i * innerW / 23);
                const txt = document.createElementNS(svg.namespaceURI,"text");
                txt.setAttribute("x", x);
                txt.setAttribute("y", H-15);
                txt.setAttribute("text-anchor", "middle");
                txt.textContent = `${i.toString().padStart(2, '0')}:00`;
                hourLabels.push(txt);
            }

            // Map measurements to timeline positions
            const pts = data.map(d => {
                const [datePart, timePart] = d[0].split(' ');
                const [hour, minute, second] = timePart.split(':').map(Number);
                const timeIndex = hour + minute/60 + second/3600;
                const x = marginX + (timeIndex * innerW / 24);
                const y = marginY + innerH - ((d[1] - minValue) / (maxValue - minValue)) * innerH;
                return `${x},${y}`;
            }).join(" ");

            svg.innerHTML = `<g>
                ${refLines.map(line => line.outerHTML).join('')}
                <polyline points="${pts}" stroke="#4caf50" stroke-width="2" fill="none"/>
            </g>`;

            const title = document.createElementNS(svg.namespaceURI,"text");
            title.setAttribute("x", W/2);
            title.setAttribute("y", 25);
            title.setAttribute("text-anchor", "middle");
            title.textContent = `CO₂ concentration (ppm) - {{title}}`;
            svg.appendChild(title);

            // Add hour labels
            hourLabels.forEach(label => svg.appendChild(label));
            {% endif %}
        })();
    </script>
</body>
</html>