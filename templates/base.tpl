{% args title="CO2 Monitor", content="" %}
<!DOCTYPE html>
<html>
<head>
    <title>{{title}}</title>
    <meta charset="utf-8">
    <style>
        body { font-family: sans-serif; margin: 20px; background: #fafafa; }
        h1 { color: #333; }
        meter { width: 200px; height: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .metric { background: #fff; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>{{title}}</h1>
    {{content}}
</body>
</html>