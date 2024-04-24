import json

# Path to the JSON file
file_path = './watch_data.json'

# Read the JSON data from the file
with open(file_path, 'r') as file:
    watches_data = json.load(file)

def is_float(value):
    """ Check if the value can be converted to a float. """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

# Initialize statistics dictionaries
statistics = {}
overall_stats = {'total': 0, 'for_sale': 0, 'sold': 0, 'total_price': 0}

for watch in watches_data:
    model = watch['Model']
    # Get the most recent price history entry
    latest_price_entry = watch['PriceHistory'][-1] if watch['PriceHistory'] else None
    latest_price = latest_price_entry['Price'] if latest_price_entry and 'Price' in latest_price_entry else None

    # Initialize model stats if not already present
    if model not in statistics:
        statistics[model] = {'total': 0, 'for_sale': 0, 'sold': 0, 'total_price': 0}

    statistics[model]['total'] += 1
    overall_stats['total'] += 1

    # Check if the watch is for sale or sold and update counts
    if is_float(latest_price):
        statistics[model]['for_sale'] += 1
        overall_stats['for_sale'] += 1
        statistics[model]['total_price'] += float(latest_price)
        overall_stats['total_price'] += float(latest_price)
    else:
        statistics[model]['sold'] += 1
        overall_stats['sold'] += 1

# Calculating averages for each model
for model, stats in statistics.items():
    total_for_sale = stats['for_sale']
    total_price = stats['total_price']
    statistics[model]['average_price'] = total_price / total_for_sale if total_for_sale else 0

# Calculating overall averages
overall_for_sale = overall_stats['for_sale']
overall_stats['average_price'] = overall_stats['total_price'] / overall_for_sale if overall_for_sale else 0

# Outputting the calculated statistics
print("Model-wise Statistics:")
for model, stats in statistics.items():
    print(f"{model}: Total - {stats['total']}, For Sale - {stats['for_sale']}, Sold - {stats['sold']}, Average Price - {stats['average_price']}")

print("\nOverall Statistics:")
print(f"Total Watches - {overall_stats['total']}, For Sale - {overall_stats['for_sale']}, Sold - {overall_stats['sold']}, Average Price - {overall_stats['average_price']}")
