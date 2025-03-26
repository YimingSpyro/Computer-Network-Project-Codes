from flask import Flask, request, jsonify, render_template_string
import datetime
import threading

app = Flask(__name__)

# Sample inventory (could be loaded from a file or database)
inventory = {
    "apple": 100,
    "banana": 150,
    "orange": 120,
}

# Global list to store logs
logs = []
# Use a reentrant lock to allow nested acquisitions
inventory_lock = threading.RLock()

def add_log(message):
    """Add a log entry with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    with inventory_lock:
        logs.append(log_entry)
    print(log_entry)

@app.route('/update-inventory', methods=['POST'])
def update_inventory():
    data = request.get_json()
    if not data or "items_sold" not in data:
        return jsonify({"error": "Invalid request, missing items_sold field"}), 400

    items_sold = data["items_sold"]
    with inventory_lock:
        for item, sold_qty in items_sold.items():
            if item in inventory:
                prev_qty = inventory[item]
                inventory[item] = max(0, inventory[item] - sold_qty)
                add_log(f"Sold {sold_qty} {item}(s): Updated from {prev_qty} to {inventory[item]}.")
            else:
                # If item is not in inventory, add it with 0 quantity (or handle differently)
                inventory[item] = 0
                add_log(f"New item '{item}' encountered. Set to 0 after selling {sold_qty}.")

    return jsonify({"message": "Inventory updated", "inventory": inventory}), 200

@app.route('/status', methods=['GET'])
def status():
    """Display the current inventory and logs via an HTML page."""
    html = """
    <html>
    <head>
        <title>Inventory Status</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2 { color: #333; }
            ul { list-style: none; padding: 0; }
            li { padding: 5px 0; }
            pre { background: #f4f4f4; padding: 10px; border: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <h1>Current Inventory</h1>
        <ul>
        {% for item, qty in inventory.items() %}
            <li><strong>{{ item }}:</strong> {{ qty }}</li>
        {% endfor %}
        </ul>
        <h2>Logs</h2>
        <pre>
{% for log in logs %}
{{ log }}
{% endfor %}
        </pre>
    </body>
    </html>
    """
    with inventory_lock:
        current_inventory = inventory.copy()
        current_logs = logs.copy()
    return render_template_string(html, inventory=current_inventory, logs=current_logs)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)
