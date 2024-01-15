import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

def format_price(price):
    """Formats the price as a comma-separated string or returns 'sold'."""
    if isinstance(price, (float, int)):
        return f"${price:,.2f}"
    return price

def create_hyperlink(url, text):
    """Creates an HTML hyperlink."""
    return f'<a href="{url}" target="_blank">{text}</a>'

def update_portfolio_statistics(statistics_path, today_str, data):
    """Updates portfolio statistics JSON file."""
    try:
        with open(statistics_path, "r+", encoding="utf-8") as file:
            all_statistics = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        all_statistics = {}

    all_statistics[today_str] = data

    with open(statistics_path, "w", encoding="utf-8") as file:
        json.dump(all_statistics, file, indent=4)

# Load the JSON file
json_file_path = 'watch_data.json'
with open(json_file_path, 'r', encoding='utf-8') as file:
    watch_data = json.load(file)

# Get today's date as a string
today_str = datetime.today().strftime('%Y-%m-%d')

# Data lists for tables and summary statistics
price_changes_data = []
new_additions_data = []
watches_sold_data = []
num_watches_sold = num_watches_added = num_watches_for_sale = 0
value_of_sold_watches = value_of_listed_watches = value_of_unsold_watches = 0

# BASE_URL - define your base URL here
BASE_URL = "https://tropicalwatch.com"

# Iterate through the watches in the JSON file
for watch in watch_data:
    last_price_entry = watch["PriceHistory"][-1]
    last_price_date = last_price_entry["Date"].split('T')[0]
    last_price = last_price_entry["Price"]

    if last_price_date == today_str:
        inventory_url = create_hyperlink(f"{BASE_URL}{watch['Inventory']}", "Link")
        if len(watch["PriceHistory"]) > 1:
            previous_price_entry = watch["PriceHistory"][-2]
            previous_price = previous_price_entry["Price"]

            formatted_last_price = format_price(last_price)
            formatted_previous_price = format_price(previous_price)

            if last_price == "sold":
                watches_sold_data.append([watch['Title'], "Sold", inventory_url])
                if isinstance(previous_price, (float, int)):
                    value_of_sold_watches += previous_price
                    num_watches_sold += 1
            else:
                price_changes_data.append([watch['Title'], formatted_previous_price, formatted_last_price, inventory_url])
        else:
            formatted_last_price = format_price(last_price)
            new_additions_data.append([watch['Title'], formatted_last_price, inventory_url])
            if isinstance(last_price, (float, int)):
                value_of_listed_watches += last_price
                num_watches_added += 1

    # Counting and valuing unsold watches
    if last_price != "sold":
        num_watches_for_sale += 1
        if isinstance(last_price, (float, int)):
            value_of_unsold_watches += last_price

# Create DataFrames for display
price_changes_df = pd.DataFrame(price_changes_data, columns=['Title', 'Old Price', 'New Price', 'Inventory URL'])
new_additions_df = pd.DataFrame(new_additions_data, columns=['Title', 'Price', 'Inventory URL'])
watches_sold_df = pd.DataFrame(watches_sold_data, columns=['Title', 'Status', 'Inventory URL'])

# Output the summary statistics with formatted values
formatted_sold_value = format_price(value_of_sold_watches)
formatted_listed_value = format_price(value_of_listed_watches)
formatted_unsold_value = format_price(value_of_unsold_watches)
print(f"\nValue of Sold Watches: {formatted_sold_value}")
print(f"Value of Listed Watches: {formatted_listed_value}")
print(f"Value of Unsold Watches: {formatted_unsold_value}")

# Portfolio statistics for the day
daily_statistics = {
    "Number of Watches For Sale": num_watches_for_sale,
    "Number of Watches Sold": num_watches_sold,
    "Number of Watches Added": num_watches_added,
    "Total Value of Watches For Sale": formatted_unsold_value,
    "Total Value of Watches Sold": formatted_sold_value,
    "Total Value of Watches Added": formatted_listed_value
}

# Update portfolio statistics JSON file
update_portfolio_statistics("portfolio_statistics.json", today_str, daily_statistics)

# Load the portfolio statistics JSON file
statistics_file_path = 'portfolio_statistics.json'
with open(statistics_file_path, 'r', encoding='utf-8') as file:
    portfolio_statistics = json.load(file)

# Extract dates and total values of watches for sale
dates = []
total_values_for_sale = []

for date, stats in portfolio_statistics.items():
    dates.append(date)
    # Convert formatted string back to float
    total_value = stats["Total Value of Watches For Sale"].replace('$', '').replace(',', '')
    total_values_for_sale.append(float(total_value))

# Sort data by date if needed
dates, total_values_for_sale = zip(*sorted(zip(dates, total_values_for_sale)))

# Plot the data
plt.figure(figsize=(10, 5))
plt.plot(dates, total_values_for_sale, marker='o', color='#009879')  # Use color that matches HTML

# Styling to match your HTML
plt.title('Total Value of Watches For Sale Over Time', fontsize=14, color='#333')
plt.xlabel('Date', fontsize=12, color='#333')
plt.ylabel('Total Value of Watches For Sale ($)', fontsize=12, color='#333')
plt.xticks(rotation=45, color='#333')
plt.yticks(color='#333')
plt.grid(True, linestyle='--', alpha=0.7)
plt.gca().set_facecolor('#f4f4f4')
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['bottom'].set_color('#333')
plt.gca().spines['left'].set_color('#333')
plt.gca().yaxis.set_major_formatter(mticker.StrMethodFormatter('${x:,.0f}'))  # Format y-axis labels

# Save the figure
plt.tight_layout()
plt.savefig('docs/portfolio_value.png', bbox_inches='tight', facecolor='#f4f4f4')
plt.close()


# Create the 'docs' directory if it does not exist
os.makedirs('docs', exist_ok=True)

# Building the HTML structure with added CSS styling
html_output = f"""
<html>
<head>
    <title>Watch Data Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            color: #333;
        }}
        h1, h2, h3 {{
            text-align: center;
            color: #333;
        }}
        table {{
            border-collapse: collapse;
            margin: 25px auto;
            font-size: 0.9em;
            min-width: 400px;
            border-radius: 5px 5px 0 0;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        }}
        table thead tr {{
            background-color: #009879;
            color: #ffffff;
            text-align: left;
        }}
        table th,
        table td {{
            padding: 12px 15px;
        }}
        table tbody tr {{
            border-bottom: 1px solid #dddddd;
        }}
        table tbody tr:nth-of-type(even) {{
            background-color: #f3f3f3;
        }}
        table tbody tr:last-of-type {{
            border-bottom: 2px solid #009879;
        }}
        .stats {{
            text-align: center;
            margin: 20px;
        }}
        img {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 75%; /* You can adjust the width as needed */
        }}
    </style>
</head>
<body>
    <h1>Watch Data Report - {today_str}</h1>
    <div class="stats">
        <h3>Summary Statistics</h3>
        <p>Value of sold Watches: {formatted_sold_value}</p>
        <p>Value of listed Watches: {formatted_listed_value}</p>
        <p>Value of unsold Watches: {formatted_unsold_value}</p>
    </div>
    <h2>Price Changes Today:</h2>
    {price_changes_df.to_html(escape=False, index=False, classes='table')}

    <h2>New Additions Today:</h2>
    {new_additions_df.to_html(escape=False, index=False, classes='table')}

    <h2>Watches Sold Today:</h2>
    {watches_sold_df.to_html(escape=False, index=False, classes='table')}

    <h2>Porfolio Value</h2>
    <img src='portfolio_value.png' alt='Brand Distribution'>
</body>
</html>
"""

# Write the HTML content to the file
with open('docs/index.html', 'w', encoding='utf-8') as file:
    file.write(html_output)
