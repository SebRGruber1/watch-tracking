import streamlit as st
import pandas as pd

# Cache the portfolio data to improve performance
@st.cache_data
def load_portfolio_data():
    try:
        data = pd.read_json("portfolio_statistics.json")
        return data
    except Exception as e:
        st.error(f"Error loading portfolio data: {e}")
        return pd.DataFrame()

# Cache the watch data to improve performance
@st.cache_data
def load_watch_data():
    try:
        data = pd.read_json("watch_data.json")
        return data
    except Exception as e:
        st.error(f"Error loading watch data: {e}")
        return pd.DataFrame()

# Preprocess portfolio data
def preprocess_portfolio_data(data):
    if data.empty:
        return pd.DataFrame()
    
    try:
        data = pd.DataFrame(data).T  # Transpose so dates become rows
        # Replace $ and , in the values and convert to float
        value_columns = [
            "Total Value of Watches For Sale", 
            "Total Value of Watches Sold", 
            "Total Value of Watches Added"
        ]
        for col in value_columns:
            if col in data.columns:
                data[col] = data[col].replace({'\$': '', ',': ''}, regex=True).astype(float)
        return data
    except Exception as e:
        st.error(f"Error preprocessing portfolio data: {e}")
        return pd.DataFrame()

# Portfolio visualizations
def plot_total_value(data):
    value_columns = [
        "Total Value of Watches For Sale", 
        "Total Value of Watches Sold", 
        "Total Value of Watches Added"
    ]
    available_columns = [col for col in value_columns if col in data.columns]
    
    if not available_columns:
        st.warning("No total value data available for plotting.")
        return
    
    st.line_chart(data[available_columns])

def plot_number_of_watches(data):
    count_columns = ["Number of Watches Sold", "Number of Watches Added"]
    available_columns = [col for col in count_columns if col in data.columns]
    
    if not available_columns:
        st.warning("No watch count data available for plotting.")
        return
    
    st.line_chart(data[available_columns])

# Watch Price Evolution Visualization
def plot_price_evolution(data):
    st.header("Watch Price Evolution Dashboard")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Model', 'Reference', 'PriceHistory', 'Title']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Brand selection
    brands = data['Brand'].dropna().unique()
    if len(brands) == 0:
        st.error("No brands available in the data.")
        return
    selected_brand = st.selectbox('Select Brand', brands)
    
    # Model selection based on selected brand
    models = data[data['Brand'] == selected_brand]['Model'].dropna().unique()
    if len(models) == 0:
        st.error(f"No models available for the brand '{selected_brand}'.")
        return
    selected_model = st.selectbox('Select Model', models)
    
    # Reference selection based on selected brand and model
    references = data[
        (data['Brand'] == selected_brand) & 
        (data['Model'] == selected_model)
    ]['Reference'].dropna().unique()
    if len(references) == 0:
        st.error(f"No references available for the brand '{selected_brand}' and model '{selected_model}'.")
        return
    selected_reference = st.selectbox('Select Reference', references)
    
    # Filter data based on selections
    filtered_data = data[
        (data['Brand'] == selected_brand) &
        (data['Model'] == selected_model) &
        (data['Reference'] == selected_reference)
    ]
    
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
            st.warning(f"Error processing watch '{row['Title']}': {e}")
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

# Watch Price Distribution Visualization
def plot_price_distribution(data):
    st.header("Watch Price Distribution")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Year', 'PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Brand selection
    brands = data['Brand'].dropna().unique()
    if len(brands) == 0:
        st.error("No brands available in the data.")
        return
    selected_brand = st.selectbox('Select Brand', brands)
    
    # Year selection based on selected brand
    years = data[data['Brand'] == selected_brand]['Year'].dropna().unique()
    if len(years) == 0:
        st.error(f"No years available for the brand '{selected_brand}'.")
        return
    selected_year = st.selectbox('Select Year', sorted(years))
    
    # Filter data based on selections
    filtered_data = data[
        (data['Brand'] == selected_brand) &
        (data['Year'] == selected_year)
    ]
    
    if filtered_data.empty:
        st.warning("No data available for the selected Brand and Year.")
        return
    
    # Extract final prices
    final_prices = []
    for _, row in filtered_data.iterrows():
        try:
            price_history = row['PriceHistory']
            if not price_history:
                continue
            last_entry = price_history[-1]
            if last_entry['Price'] != 'sold':
                final_price = last_entry['Price']
            else:
                if len(price_history) < 2:
                    continue  # No valid price before sold
                final_price = price_history[-2]['Price']
            final_prices.append(final_price)
        except Exception as e:
            st.warning(f"Error processing watch '{row.get('Title', 'Unknown')}': {e}")
            continue
    
    if not final_prices:
        st.warning("No valid final prices available for plotting.")
        return
    
    final_prices_df = pd.DataFrame(final_prices, columns=['Final Price'])
    
    # Plot price distribution using bar_chart
    price_counts = final_prices_df['Final Price'].value_counts().sort_index()
    st.bar_chart(price_counts)
    
    st.write(f"**Showing price distribution for {selected_brand} in {selected_year}**")

# Watch Time to Sell Visualization
def plot_time_to_sell(data):
    st.header("Time to Sell Distribution")
    
    # Ensure required columns exist
    required_columns = ['PriceHistory']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    time_to_sell = []
    
    for _, row in data.iterrows():
        try:
            price_history = row['PriceHistory']
            if not price_history or len(price_history) < 2:
                continue
            if price_history[-1]['Price'] == 'sold':
                start_date = pd.to_datetime(price_history[0]['Date'], errors='coerce')
                sold_date = pd.to_datetime(price_history[-1]['Date'], errors='coerce')
                if pd.isna(start_date) or pd.isna(sold_date):
                    continue
                days_to_sell = (sold_date - start_date).days
                if days_to_sell >= 0:
                    time_to_sell.append(days_to_sell)
        except Exception as e:
            st.warning(f"Error processing watch '{row.get('Title', 'Unknown')}': {e}")
            continue
    
    if not time_to_sell:
        st.warning("No valid time to sell data available for plotting.")
        return
    
    time_to_sell_df = pd.DataFrame(time_to_sell, columns=['Days to Sell'])
    
    # Plot using Streamlit's bar_chart
    time_counts = time_to_sell_df['Days to Sell'].value_counts().sort_index()
    st.bar_chart(time_counts)
    
    st.write("**Distribution of time to sell for watches.**")

# Watch Top Brands Visualization
def plot_top_brands(data):
    st.header("Top Selling Brands")
    
    # Ensure required columns exist
    required_columns = ['Brand', 'Year']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in watch data: {', '.join(missing_columns)}")
        return
    
    # Year selection
    years = data['Year'].dropna().unique()
    if len(years) == 0:
        st.error("No years available in the data.")
        return
    selected_year = st.selectbox('Select Year', sorted(years))
    
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
    st.bar_chart(brand_sales)
    
    st.write(f"**Top selling brands in {selected_year}.**")

# Watch Price Comparison Visualization
def plot_price_comparison(data):
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
        def get_final_price(price_history):
            if not price_history:
                return None
            last_entry = price_history[-1]
            if last_entry['Price'] != 'sold':
                return last_entry['Price']
            elif len(price_history) >= 2:
                return price_history[-2]['Price']
            else:
                return None
        
        data['FinalPrice'] = data['PriceHistory'].apply(get_final_price)
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
    st.bar_chart(avg_price_per_brand)
    
    st.write("**Average Final Price Comparison Across Brands.**")

# Streamlit App Layout
def main():
    st.sidebar.title("Watch Data and Portfolio Analysis")
    page = st.sidebar.selectbox("Choose a page", ["Portfolio Analysis", "Watch Data Analysis"])
    
    if page == "Portfolio Analysis":
        st.title("Portfolio Data Visual Analysis")
        data = load_portfolio_data()
        data = preprocess_portfolio_data(data)
        
        # Display raw data
        if st.checkbox('Show Raw Portfolio Data'):
            st.write(data)
        
        # Portfolio Visualizations
        st.subheader("Total Value of Watches Over Time")
        plot_total_value(data)

        st.subheader("Watches Sold and Added Over Time")
        plot_number_of_watches(data)
    
    elif page == "Watch Data Analysis":
        st.title("Watch Data Visual Analysis")
        data = load_watch_data()
        
        if data.empty:
            st.warning("Watch data is empty or failed to load.")
            return
        
        # Watch Visualizations
        analysis_type = st.sidebar.selectbox(
            "Select Analysis Type", 
            [
                "Price Evolution", 
                "Price Distribution", 
                "Time to Sell", 
                "Top Brands", 
                "Price Comparison"
            ]
        )
        
        if analysis_type == "Price Evolution":
            plot_price_evolution(data)
        
        elif analysis_type == "Price Distribution":
            plot_price_distribution(data)
        
        elif analysis_type == "Time to Sell":
            plot_time_to_sell(data)
        
        elif analysis_type == "Top Brands":
            plot_top_brands(data)
        
        elif analysis_type == "Price Comparison":
            plot_price_comparison(data)

if __name__ == "__main__":
    main()
