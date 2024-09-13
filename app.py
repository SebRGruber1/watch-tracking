import streamlit as st
import pandas as pd

# Constants for column names to avoid typos
PORTFOLIO_VALUE_COLUMNS = [
    "Total Value of Watches For Sale", 
    "Total Value of Watches Sold", 
    "Total Value of Watches Added"
]

PORTFOLIO_COUNT_COLUMNS = [
    "Number of Watches Sold", 
    "Number of Watches Added"
]

WATCH_REQUIRED_COLUMNS = [
    "Brand", 
    "Model", 
    "Reference", 
    "PriceHistory", 
    "Title"
]

# Helper Functions

@st.cache_data
def load_json_data(file_path):
    """Load JSON data from a file."""
    try:
        data = pd.read_json(file_path)
        return data
    except ValueError as ve:
        st.error(f"ValueError loading {file_path}: {ve}")
    except FileNotFoundError:
        st.error(f"File {file_path} not found.")
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
    return pd.DataFrame()

def preprocess_portfolio_data(data):
    """Preprocess the portfolio data by cleaning value columns."""
    if data.empty:
        st.error("Portfolio data is empty.")
        return pd.DataFrame()
    
    try:
        data = data.transpose()  # Transpose so dates become rows
        # Clean value columns
        for col in PORTFOLIO_VALUE_COLUMNS:
            if col in data.columns:
                data[col] = data[col].replace({'\$': '', ',': ''}, regex=True).astype(float)
        return data
    except Exception as e:
        st.error(f"Error preprocessing portfolio data: {e}")
        return pd.DataFrame()

def select_filter(data, filter_name, options, label):
    """Create a selectbox filter and return the selected option."""
    if len(options) == 0:
        st.error(f"No {filter_name} available.")
        return None
    selected = st.selectbox(f"Select {label}", options)
    return selected

def filter_watch_data(data, brand, model, reference):
    """Filter the watch data based on brand, model, and reference."""
    return data[
        (data['Brand'] == brand) &
        (data['Model'] == model) &
        (data['Reference'] == reference)
    ]

def extract_final_price(price_history):
    """Extract the final price from the price history."""
    if not price_history:
        return None
    try:
        last_entry = price_history[-1]
        if last_entry['Price'] != 'sold':
            return last_entry['Price']
        elif len(price_history) >= 2:
            return price_history[-2]['Price']
    except Exception:
        return None
    return None

def extract_days_to_sell(price_history):
    """Calculate days to sell based on price history."""
    if not price_history or len(price_history) < 2:
        return None
    try:
        if price_history[-1]['Price'] == 'sold':
            start_date = pd.to_datetime(price_history[0]['Date'], errors='coerce')
            sold_date = pd.to_datetime(price_history[-1]['Date'], errors='coerce')
            if pd.isna(start_date) or pd.isna(sold_date):
                return None
            days_to_sell = (sold_date - start_date).days
            if days_to_sell >= 0:
                return days_to_sell
    except Exception:
        return None
    return None

def plot_line_chart(data, columns, title, subtitle):
    """Plot a line chart with given data and columns."""
    if not all(col in data.columns for col in columns):
        st.warning(f"Missing columns for {title}.")
        return
    st.subheader(subtitle)
    st.line_chart(data[columns])
    st.write(f"**{title}**")

def plot_bar_chart(data, x, title, subtitle):
    """Plot a bar chart with given data."""
    if x not in data.columns:
        st.warning(f"Missing column '{x}' for {title}.")
        return
    st.subheader(subtitle)
    counts = data[x].value_counts().sort_index()
    st.bar_chart(counts)
    st.write(f"**{title}**")

# Portfolio Visualization Functions

def plot_total_value(data):
    """Plot total value of watches over time."""
    available_columns = [col for col in PORTFOLIO_VALUE_COLUMNS if col in data.columns]
    if not available_columns:
        st.warning("No total value data available for plotting.")
        return
    st.subheader("Total Value of Watches Over Time")
    st.line_chart(data[available_columns])

def plot_number_of_watches(data):
    """Plot number of watches sold and added over time."""
    available_columns = [col for col in PORTFOLIO_COUNT_COLUMNS if col in data.columns]
    if not available_columns:
        st.warning("No watch count data available for plotting.")
        return
    st.subheader("Watches Sold and Added Over Time")
    st.line_chart(data[available_columns])

def plot_daily_summary(data):
    """Display a summary of watches added, sold, and price changes in a day."""
    st.subheader("Daily Summary")
    
    # Assuming the portfolio data has a Date index
    if not isinstance(data.index, pd.DatetimeIndex):
        st.error("Portfolio data index is not datetime.")
        return
    
    selected_date = st.date_input("Select Date", data.index.max().date())
    selected_data = data.loc[data.index.date == selected_date]
    
    if selected_data.empty:
        st.warning("No data available for the selected date.")
        return
    
    # Summarize watches added, sold, and price changes
    watches_added = selected_data.get("Number of Watches Added", 0).sum()
    watches_sold = selected_data.get("Number of Watches Sold", 0).sum()
    price_added = selected_data.get("Total Value of Watches Added", 0).sum()
    price_sold = selected_data.get("Total Value of Watches Sold", 0).sum()
    
    st.metric(label="Watches Added", value=watches_added)
    st.metric(label="Watches Sold", value=watches_sold)
    st.metric(label="Total Value Added ($)", value=f"{price_added:,.2f}")
    st.metric(label="Total Value Sold ($)", value=f"{price_sold:,.2f}")

# Watch Data Visualization Functions

def plot_price_evolution(data):
    """Plot the price evolution of watches based on selected Brand, Model, and Reference."""
    st.header("Watch Price Evolution Dashboard")
    
    # Ensure required columns exist
    missing_columns = [col for col in WATCH_REQUIRED_COLUMNS if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Brand selection
    brands = data['Brand'].dropna().unique()
    selected_brand = select_filter(data, "brands", brands, "Brand")
    if not selected_brand:
        return
    
    # Model selection based on selected brand
    models = data[data['Brand'] == selected_brand]['Model'].dropna().unique()
    selected_model = select_filter(data, "models", models, "Model")
    if not selected_model:
        return
    
    # Reference selection based on selected brand and model
    references = data[
        (data['Brand'] == selected_brand) & 
        (data['Model'] == selected_model)
    ]['Reference'].dropna().unique()
    selected_reference = select_filter(data, "references", references, "Reference")
    if not selected_reference:
        return
    
    # Filter data based on selections
    filtered_data = filter_watch_data(data, selected_brand, selected_model, selected_reference)
    
    if filtered_data.empty:
        st.warning("No data available for the selected Brand, Model, and Reference.")
        return
    
    # Collect all price histories
    price_dfs = []
    for _, row in filtered_data.iterrows():
        try:
            price_history = pd.DataFrame(row['PriceHistory'])
            
            # Convert "sold" to NaN and drop those rows
            price_history['Price'] = pd.to_numeric(price_history['Price'], errors='coerce')
            price_history = price_history.dropna(subset=['Price'])
            
            # Convert Date column to datetime
            price_history['Date'] = pd.to_datetime(price_history['Date'], errors='coerce')
            price_history = price_history.dropna(subset=['Date'])
            
            if price_history.empty:
                continue  # Skip if no valid price history
            
            # Sort by Date
            price_history = price_history.sort_values('Date')
            
            # Add a column for the watch title
            price_history['Title'] = row['Title']
            
            # Select relevant columns
            price_dfs.append(price_history[['Date', 'Price', 'Title']])
        except Exception as e:
            st.warning(f"Error processing watch '{row.get('Title', 'Unknown')}': {e}")
            continue
    
    if not price_dfs:
        st.warning("No valid price history data available after processing.")
        return
    
    # Concatenate all price histories
    all_prices = pd.concat(price_dfs)
    
    # Pivot the data to have Dates as index and Titles as columns
    try:
        all_prices_pivot = all_prices.pivot(index='Date', columns='Title', values='Price')
    except Exception as e:
        st.error(f"Error pivoting price data: {e}")
        return
    
    # Sort the index
    all_prices_pivot = all_prices_pivot.sort_index()
    
    # Forward-fill the NaN values to maintain the last known price
    all_prices_pivot = all_prices_pivot.ffill()
    
    if all_prices_pivot.empty:
        st.warning("No data available to plot after pivoting.")
        return
    
    # Plot using Streamlit's line_chart
    st.subheader("Price Evolution Chart")
    st.line_chart(all_prices_pivot)
    
    st.write(f"**Showing price evolution for:** {selected_brand} {selected_model} (Reference: {selected_reference})")

def plot_price_distribution(data):
    """Plot the price distribution of watches based on selected Brand and Year."""
    st.header("Watch Price Distribution")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Year', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Brand selection
    brands = data['Brand'].dropna().unique()
    selected_brand = select_filter(data, "brands", brands, "Brand")
    if not selected_brand:
        return
    
    # Year selection based on selected brand
    years = data[data['Brand'] == selected_brand]['Year'].dropna().unique()
    selected_year = select_filter(data, "years", sorted(years), "Year")
    if not selected_year:
        return
    
    # Filter data based on selections
    filtered_data = data[
        (data['Brand'] == selected_brand) &
        (data['Year'] == selected_year)
    ]
    
    if filtered_data.empty:
        st.warning("No data available for the selected Brand and Year.")
        return
    
    # Extract final prices
    final_prices = filtered_data['PriceHistory'].apply(extract_final_price).dropna().tolist()
    
    if not final_prices:
        st.warning("No valid final prices available for plotting.")
        return
    
    final_prices_df = pd.DataFrame(final_prices, columns=['Final Price'])
    
    # Plot price distribution using bar_chart
    price_counts = final_prices_df['Final Price'].value_counts().sort_index()
    st.subheader("Price Distribution Chart")
    st.bar_chart(price_counts)
    
    st.write(f"**Showing price distribution for {selected_brand} in {selected_year}**")

def plot_time_to_sell(data):
    """Plot the distribution of time taken to sell watches."""
    st.header("Time to Sell Distribution")
    
    # Ensure required columns exist
    required_columns = ['PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Extract days to sell
    days_to_sell = data['PriceHistory'].apply(extract_days_to_sell).dropna().tolist()
    
    if not days_to_sell:
        st.warning("No valid time to sell data available for plotting.")
        return
    
    time_to_sell_df = pd.DataFrame(days_to_sell, columns=['Days to Sell'])
    
    # Plot using Streamlit's bar_chart
    time_counts = time_to_sell_df['Days to Sell'].value_counts().sort_index()
    st.subheader("Time to Sell Chart")
    st.bar_chart(time_counts)
    
    st.write("**Distribution of time to sell for watches.**")

def plot_top_brands(data):
    """Plot the top selling brands for a selected year."""
    st.header("Top Selling Brands")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Year']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Year selection
    years = data['Year'].dropna().unique()
    selected_year = select_filter(data, "years", sorted(years), "Year")
    if not selected_year:
        return
    
    # Filter data based on selected year
    filtered_data = data[data['Year'] == selected_year]
    
    if filtered_data.empty:
        st.warning("No data available for the selected Year.")
        return
    
    # Count sales per brand
    brand_sales = filtered_data['Brand'].value_counts()
    
    if brand_sales.empty:
        st.warning("No brand sales data available for plotting.")
        return
    
    # Plot using Streamlit's bar_chart
    st.subheader("Top Selling Brands Chart")
    st.bar_chart(brand_sales)
    
    st.write(f"**Top selling brands in {selected_year}.**")

def plot_price_comparison(data):
    """Plot the average final price across different brands."""
    st.header("Price Comparison Across Brands")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Calculate Final Price
    try:
        data = data.copy()
        data['FinalPrice'] = data['PriceHistory'].apply(extract_final_price)
        data = data.dropna(subset=['FinalPrice'])
    except Exception as e:
        st.error(f"Error calculating final prices: {e}")
        return
    
    if data.empty:
        st.warning("No final price data available for comparison.")
        return
    
    # Group by brand and calculate average price
    try:
        avg_price_per_brand = data.groupby('Brand')['FinalPrice'].mean().sort_values(ascending=False)
    except Exception as e:
        st.error(f"Error calculating average prices: {e}")
        return
    
    if avg_price_per_brand.empty:
        st.warning("No average price data available for plotting.")
        return
    
    # Plot using Streamlit's bar_chart
    st.subheader("Average Final Price Comparison Chart")
    st.bar_chart(avg_price_per_brand)
    
    st.write("**Average Final Price Comparison Across Brands.**")

def plot_average_price_over_time(data):
    """Plot average price over time by brand and model."""
    st.header("Average Price Over Time by Brand and Model")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Model', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Select Brand
    brands = data['Brand'].dropna().unique()
    selected_brand = select_filter(data, "brands", brands, "Brand")
    if not selected_brand:
        return
    
    # Select Model based on Brand
    models = data[data['Brand'] == selected_brand]['Model'].dropna().unique()
    selected_model = select_filter(data, "models", models, "Model")
    if not selected_model:
        return
    
    # Filter data
    filtered_data = data[
        (data['Brand'] == selected_brand) &
        (data['Model'] == selected_model)
    ]
    
    if filtered_data.empty:
        st.warning("No data available for the selected Brand and Model.")
        return
    
    # Extract price histories with dates
    price_dfs = []
    for _, row in filtered_data.iterrows():
        try:
            price_history = pd.DataFrame(row['PriceHistory'])
            price_history['Price'] = pd.to_numeric(price_history['Price'], errors='coerce')
            price_history = price_history.dropna(subset=['Price'])
            price_history['Date'] = pd.to_datetime(price_history['Date'], errors='coerce')
            price_history = price_history.dropna(subset=['Date'])
            if price_history.empty:
                continue
            price_history = price_history.sort_values('Date')
            price_history['Title'] = row['Title']
            price_dfs.append(price_history[['Date', 'Price', 'Title']])
        except Exception:
            continue
    
    if not price_dfs:
        st.warning("No valid price history data available.")
        return
    
    all_prices = pd.concat(price_dfs)
    
    # Resample to monthly average
    all_prices['Month'] = all_prices['Date'].dt.to_period('M')
    monthly_avg = all_prices.groupby('Month')['Price'].mean().reset_index()
    monthly_avg['Month'] = monthly_avg['Month'].dt.to_timestamp()
    
    # Plot
    st.subheader("Monthly Average Price Chart")
    st.line_chart(monthly_avg.set_index('Month'))
    
    st.write(f"**Showing monthly average price for {selected_brand} {selected_model}.**")

def plot_price_trend_comparison(data):
    """Compare price trends between different brands."""
    st.header("Price Trend Comparison Between Brands")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Select multiple brands
    brands = data['Brand'].dropna().unique()
    selected_brands = st.multiselect("Select Brands to Compare", brands, default=brands[:2])
    
    if not selected_brands:
        st.warning("Please select at least one brand.")
        return
    
    # Filter data
    filtered_data = data[data['Brand'].isin(selected_brands)]
    
    if filtered_data.empty:
        st.warning("No data available for the selected brands.")
        return
    
    # Extract average price over time for each brand
    trend_data = {}
    for brand in selected_brands:
        brand_data = filtered_data[filtered_data['Brand'] == brand]
        price_dfs = []
        for _, row in brand_data.iterrows():
            try:
                price_history = pd.DataFrame(row['PriceHistory'])
                price_history['Price'] = pd.to_numeric(price_history['Price'], errors='coerce')
                price_history = price_history.dropna(subset=['Price'])
                price_history['Date'] = pd.to_datetime(price_history['Date'], errors='coerce')
                price_history = price_history.dropna(subset=['Date'])
                if price_history.empty:
                    continue
                price_history = price_history.sort_values('Date')
                price_history['Brand'] = brand
                price_dfs.append(price_history[['Date', 'Price', 'Brand']])
            except Exception:
                continue
        if price_dfs:
            brand_prices = pd.concat(price_dfs)
            brand_prices.set_index('Date', inplace=True)
            monthly_avg = brand_prices.resample('M').mean()
            trend_data[brand] = monthly_avg['Price']
    
    if not trend_data:
        st.warning("No valid price history data available for the selected brands.")
        return
    
    trend_df = pd.DataFrame(trend_data)
    
    # Plot
    st.subheader("Monthly Average Price Trend Comparison")
    st.line_chart(trend_df)
    
    st.write("**Comparing monthly average price trends between selected brands.**")

def plot_price_change_heatmap(data):
    """Plot a heatmap of price changes across brands and models."""
    st.header("Price Change Heatmap")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Model', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Select Brand and Model
    brands = data['Brand'].dropna().unique()
    selected_brand = select_filter(data, "brands", brands, "Brand")
    if not selected_brand:
        return
    
    models = data[data['Brand'] == selected_brand]['Model'].dropna().unique()
    selected_model = select_filter(data, "models", models, "Model")
    if not selected_model:
        return
    
    # Filter data
    filtered_data = data[
        (data['Brand'] == selected_brand) &
        (data['Model'] == selected_model)
    ]
    
    if filtered_data.empty:
        st.warning("No data available for the selected Brand and Model.")
        return
    
    # Calculate price changes
    price_changes = []
    for _, row in filtered_data.iterrows():
        try:
            price_history = row['PriceHistory']
            if len(price_history) < 2:
                continue
            changes = [price_history[i]['Price'] - price_history[i-1]['Price'] 
                       for i in range(1, len(price_history)) 
                       if price_history[i]['Price'] != 'sold' and price_history[i-1]['Price'] != 'sold']
            if changes:
                avg_change = sum(changes) / len(changes)
                price_changes.append(avg_change)
        except Exception:
            continue
    
    if not price_changes:
        st.warning("No price changes available for plotting.")
        return
    
    # Create a DataFrame for heatmap
    heatmap_data = pd.DataFrame({
        'Brand': selected_brand,
        'Model': selected_model,
        'Average Price Change': price_changes
    })
    
    # Pivot for heatmap
    heatmap_pivot = heatmap_data.pivot_table(index='Brand', columns='Model', values='Average Price Change')
    
    # Plot heatmap using Streamlit's built-in visualization
    st.subheader("Average Price Change Heatmap")
    st.dataframe(heatmap_pivot.style.background_gradient(cmap='coolwarm'))
    
    st.write("**Heatmap showing average price changes between successive sales for selected Brand and Model.**")

def plot_median_time_to_sell(data):
    """Plot the median time to sell watches by brand and model."""
    st.header("Median Time to Sell by Brand and Model")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Model', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Calculate days to sell
    data = data.copy()
    data['DaysToSell'] = data['PriceHistory'].apply(extract_days_to_sell)
    data = data.dropna(subset=['DaysToSell'])
    
    if data.empty:
        st.warning("No data available for calculating time to sell.")
        return
    
    # Group by Brand and Model and calculate median
    median_days = data.groupby(['Brand', 'Model'])['DaysToSell'].median().reset_index()
    
    if median_days.empty:
        st.warning("No median time to sell data available.")
        return
    
    # Pivot for better visualization
    median_pivot = median_days.pivot(index='Brand', columns='Model', values='DaysToSell')
    
    st.subheader("Median Time to Sell Chart")
    st.dataframe(median_pivot.style.background_gradient(cmap='YlGnBu'))
    
    st.write("**Table showing the median number of days taken to sell watches by Brand and Model.**")

def plot_yearly_sales_volume_revenue(data):
    """Plot yearly sales volume and revenue."""
    st.header("Yearly Sales Volume and Revenue")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Extract year from sale date
    sales = []
    for _, row in data.iterrows():
        try:
            price_history = row['PriceHistory']
            for entry in price_history:
                if entry['Price'] == 'sold':
                    sale_date = pd.to_datetime(entry['Date'], errors='coerce')
                    if pd.isna(sale_date):
                        continue
                    sales.append({
                        'Year': sale_date.year,
                        'Brand': row['Brand'],
                        'SalePrice': row['PriceHistory'][-2]['Price'] if len(row['PriceHistory']) >=2 else None
                    })
        except Exception:
            continue
    
    if not sales:
        st.warning("No sales data available for plotting.")
        return
    
    sales_df = pd.DataFrame(sales).dropna(subset=['SalePrice'])
    
    # Group by Year
    yearly_volume = sales_df.groupby('Year').size()
    yearly_revenue = sales_df.groupby('Year')['SalePrice'].sum()
    
    # Combine into a single DataFrame
    yearly_data = pd.DataFrame({
        'Sales Volume': yearly_volume,
        'Total Revenue ($)': yearly_revenue
    })
    
    # Plot
    st.subheader("Yearly Sales Volume and Revenue Chart")
    st.line_chart(yearly_data)
    
    st.write("**Line chart showing the number of watches sold and total revenue generated each year.**")

def plot_top_5_appreciated_depreciated(data):
    """Plot top 5 most appreciated and depreciated watches."""
    st.header("Top 5 Most Appreciated and Depreciated Watches")
    
    # Ensure required columns exist
    required_columns = ['PriceHistory', 'Title']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Calculate price appreciation/depreciation
    data = data.copy()
    data['PriceChange'] = data['PriceHistory'].apply(lambda x: x[-1]['Price'] - x[0]['Price'] if len(x) >=2 and x[-1]['Price'] != 'sold' else None)
    data = data.dropna(subset=['PriceChange'])
    
    if data.empty:
        st.warning("No price change data available.")
        return
    
    # Top 5 Appreciated
    top_appreciated = data.nlargest(5, 'PriceChange')[['Title', 'PriceChange']]
    
    # Top 5 Depreciated
    top_depreciated = data.nsmallest(5, 'PriceChange')[['Title', 'PriceChange']]
    
    # Display
    st.subheader("Top 5 Most Appreciated Watches")
    st.table(top_appreciated)
    
    st.subheader("Top 5 Most Depreciated Watches")
    st.table(top_depreciated)
    
    st.write("**Tables showing the top 5 watches with the highest price appreciation and depreciation.**")

# Watch Price Trend Comparison Between Brands
def plot_price_trend_comparison(data):
    """Compare price trends between different brands."""
    st.header("Price Trend Comparison Between Brands")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Select multiple brands
    brands = data['Brand'].dropna().unique()
    selected_brands = st.multiselect("Select Brands to Compare", brands, default=brands[:2])
    
    if not selected_brands:
        st.warning("Please select at least one brand.")
        return
    
    # Filter data
    filtered_data = data[data['Brand'].isin(selected_brands)]
    
    if filtered_data.empty:
        st.warning("No data available for the selected brands.")
        return
    
    # Extract average price over time for each brand
    trend_data = {}
    for brand in selected_brands:
        brand_data = filtered_data[filtered_data['Brand'] == brand]
        price_dfs = []
        for _, row in brand_data.iterrows():
            try:
                price_history = pd.DataFrame(row['PriceHistory'])
                price_history['Price'] = pd.to_numeric(price_history['Price'], errors='coerce')
                price_history = price_history.dropna(subset=['Price'])
                price_history['Date'] = pd.to_datetime(price_history['Date'], errors='coerce')
                price_history = price_history.dropna(subset=['Date'])
                if price_history.empty:
                    continue
                price_history = price_history.sort_values('Date')
                price_history['Brand'] = brand
                price_dfs.append(price_history[['Date', 'Price', 'Brand']])
            except Exception:
                continue
        if price_dfs:
            brand_prices = pd.concat(price_dfs)
            brand_prices.set_index('Date', inplace=True)
            monthly_avg = brand_prices.resample('M').mean()
            trend_data[brand] = monthly_avg['Price']
    
    if not trend_data:
        st.warning("No valid price history data available for the selected brands.")
        return
    
    trend_df = pd.DataFrame(trend_data)
    
    # Plot
    st.subheader("Monthly Average Price Trend Comparison")
    st.line_chart(trend_df)
    
    st.write("**Comparing monthly average price trends between selected brands.**")

# Price Trend Comparison Function was already added

def plot_price_change_heatmap(data):
    """Plot a heatmap of price changes across brands and models."""
    st.header("Price Change Heatmap")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Model', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Select Brand and Model
    brands = data['Brand'].dropna().unique()
    selected_brand = select_filter(data, "brands", brands, "Brand")
    if not selected_brand:
        return
    
    models = data[data['Brand'] == selected_brand]['Model'].dropna().unique()
    selected_model = select_filter(data, "models", models, "Model")
    if not selected_model:
        return
    
    # Filter data
    filtered_data = data[
        (data['Brand'] == selected_brand) &
        (data['Model'] == selected_model)
    ]
    
    if filtered_data.empty:
        st.warning("No data available for the selected Brand and Model.")
        return
    
    # Calculate price changes
    price_changes = []
    for _, row in filtered_data.iterrows():
        try:
            price_history = row['PriceHistory']
            if len(price_history) < 2:
                continue
            changes = [price_history[i]['Price'] - price_history[i-1]['Price'] 
                       for i in range(1, len(price_history)) 
                       if price_history[i]['Price'] != 'sold' and price_history[i-1]['Price'] != 'sold']
            if changes:
                avg_change = sum(changes) / len(changes)
                price_changes.append(avg_change)
        except Exception:
            continue
    
    if not price_changes:
        st.warning("No price changes available for plotting.")
        return
    
    # Create a DataFrame for heatmap
    heatmap_data = pd.DataFrame({
        'Brand': selected_brand,
        'Model': selected_model,
        'Average Price Change': price_changes
    })
    
    # Pivot for heatmap
    heatmap_pivot = heatmap_data.pivot_table(index='Brand', columns='Model', values='Average Price Change')
    
    # Plot heatmap using Streamlit's built-in visualization
    st.subheader("Average Price Change Heatmap")
    st.dataframe(heatmap_pivot.style.background_gradient(cmap='coolwarm'))
    
    st.write("**Heatmap showing average price changes between successive sales for selected Brand and Model.**")

def plot_median_time_to_sell(data):
    """Plot the median time to sell watches by brand and model."""
    st.header("Median Time to Sell by Brand and Model")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Model', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Calculate days to sell
    data = data.copy()
    data['DaysToSell'] = data['PriceHistory'].apply(extract_days_to_sell)
    data = data.dropna(subset=['DaysToSell'])
    
    if data.empty:
        st.warning("No data available for calculating time to sell.")
        return
    
    # Group by Brand and Model and calculate median
    median_days = data.groupby(['Brand', 'Model'])['DaysToSell'].median().reset_index()
    
    if median_days.empty:
        st.warning("No median time to sell data available.")
        return
    
    # Pivot for better visualization
    median_pivot = median_days.pivot_table(index='Brand', columns='Model', values='DaysToSell')
    
    st.subheader("Median Time to Sell Chart")
    st.dataframe(median_pivot.style.background_gradient(cmap='YlGnBu'))
    
    st.write("**Table showing the median number of days taken to sell watches by Brand and Model.**")

def plot_yearly_sales_volume_revenue(data):
    """Plot yearly sales volume and revenue."""
    st.header("Yearly Sales Volume and Revenue")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Extract year from sale date
    sales = []
    for _, row in data.iterrows():
        try:
            price_history = row['PriceHistory']
            for entry in price_history:
                if entry['Price'] == 'sold':
                    sale_date = pd.to_datetime(entry['Date'], errors='coerce')
                    if pd.isna(sale_date):
                        continue
                    sale_price = extract_final_price(price_history)
                    if sale_price is None:
                        continue
                    sales.append({
                        'Year': sale_date.year,
                        'Brand': row['Brand'],
                        'SalePrice': sale_price
                    })
        except Exception:
            continue
    
    if not sales:
        st.warning("No sales data available for plotting.")
        return
    
    sales_df = pd.DataFrame(sales).dropna(subset=['SalePrice'])
    
    # Group by Year
    yearly_volume = sales_df.groupby('Year').size()
    yearly_revenue = sales_df.groupby('Year')['SalePrice'].sum()
    
    # Combine into a single DataFrame
    yearly_data = pd.DataFrame({
        'Sales Volume': yearly_volume,
        'Total Revenue ($)': yearly_revenue
    })
    
    # Plot
    st.subheader("Yearly Sales Volume and Revenue Chart")
    st.line_chart(yearly_data)
    
    st.write("**Line chart showing the number of watches sold and total revenue generated each year.**")

def plot_top_5_appreciated_depreciated(data):
    """Plot top 5 most appreciated and depreciated watches."""
    st.header("Top 5 Most Appreciated and Depreciated Watches")
    
    # Ensure required columns exist
    required_columns = ['PriceHistory', 'Title']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Calculate price appreciation/depreciation
    data = data.copy()
    data['PriceChange'] = data['PriceHistory'].apply(lambda x: x[-1]['Price'] - x[0]['Price'] if len(x) >=2 and x[-1]['Price'] != 'sold' else None)
    data = data.dropna(subset=['PriceChange'])
    
    if data.empty:
        st.warning("No price change data available.")
        return
    
    # Top 5 Appreciated
    top_appreciated = data.nlargest(5, 'PriceChange')[['Title', 'PriceChange']]
    
    # Top 5 Depreciated
    top_depreciated = data.nsmallest(5, 'PriceChange')[['Title', 'PriceChange']]
    
    # Display
    st.subheader("Top 5 Most Appreciated Watches")
    st.table(top_appreciated)
    
    st.subheader("Top 5 Most Depreciated Watches")
    st.table(top_depreciated)
    
    st.write("**Tables showing the top 5 watches with the highest price appreciation and depreciation.**")

# Streamlit App Layout

def main():
    st.sidebar.title("Watch Data and Portfolio Analysis")
    page = st.sidebar.selectbox("Choose a page", ["Portfolio Analysis", "Watch Data Analysis"])
    
    if page == "Portfolio Analysis":
        st.title("Portfolio Data Visual Analysis")
        portfolio_data = load_json_data("portfolio_statistics.json")
        portfolio_data = preprocess_portfolio_data(portfolio_data)
        
        if portfolio_data.empty:
            st.warning("No portfolio data available.")
            return
        
        # Display raw data
        if st.checkbox('Show Raw Portfolio Data'):
            st.write(portfolio_data)
        
        # Portfolio Visualizations
        plot_total_value(portfolio_data)
        plot_number_of_watches(portfolio_data)
        
        # Daily Summary
        plot_daily_summary(portfolio_data)
        
    elif page == "Watch Data Analysis":
        st.title("Watch Data Visual Analysis")
        watch_data = load_json_data("watch_data.json")
        
        if watch_data.empty:
            st.warning("Watch data is empty or failed to load.")
            return
        
        # Ensure required columns are present
        required_watch_columns = ['Brand', 'Model', 'Reference', 'PriceHistory', 'Title']
        missing_watch_columns = [col for col in required_watch_columns if col not in watch_data.columns]
        if missing_watch_columns:
            st.error(f"Missing columns in watch data: {', '.join(missing_watch_columns)}")
            return
        
        # Watch Visualizations
        analysis_options = {
            "Price Evolution": plot_price_evolution,
            "Price Distribution": plot_price_distribution,
            "Time to Sell": plot_time_to_sell,
            "Top Brands": plot_top_brands,
            "Price Comparison": plot_price_comparison,
            "Average Price Over Time by Brand and Model": plot_average_price_over_time,
            "Price Trend Comparison Between Brands": plot_price_trend_comparison,
            "Price Change Heatmap": plot_price_change_heatmap,
            "Median Time to Sell by Brand and Model": plot_median_time_to_sell,
            "Yearly Sales Volume and Revenue": plot_yearly_sales_volume_revenue,
            "Top 5 Most Appreciated and Depreciated Watches": plot_top_5_appreciated_depreciated
        }
        
        analysis_type = st.sidebar.selectbox(
            "Select Analysis Type", 
            list(analysis_options.keys())
        )
        
        # Execute the selected analysis
        analysis_function = analysis_options.get(analysis_type)
        if analysis_function:
            analysis_function(watch_data)
        else:
            st.error("Selected analysis type is not available.")
    
    # Footer or Additional Information
    st.sidebar.markdown("""
    ---
    **Developed by Your Name**
    """)

if __name__ == "__main__":
    main()
