import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the portfolio data
@st.cache_data
def load_portfolio_data():
    return pd.read_json("portfolio_statistics.json")

# Load the watch data
@st.cache_data
def load_watch_data():
    return pd.read_json("watch_data.json")

# Preprocess portfolio data
def preprocess_portfolio_data(data):
    data = pd.DataFrame(data).T  # Transpose the data so dates become rows
    # Replace $ and , in the values and convert to float
    for col in ["Total Value of Watches For Sale", "Total Value of Watches Sold", "Total Value of Watches Added"]:
        if col in data.columns:
            data[col] = data[col].replace({'\$': '', ',': ''}, regex=True).astype(float)
    return data

# Portfolio visualizations
def plot_total_value(data):
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Total Value of Watches For Sale'], label="For Sale")
    plt.plot(data.index, data['Total Value of Watches Sold'], label="Sold")
    plt.plot(data.index, data['Total Value of Watches Added'], label="Added")
    plt.xlabel('Date')
    plt.ylabel('Total Value (USD)')
    plt.title('Total Value of Watches Over Time')
    plt.legend()
    st.pyplot(plt)

def plot_number_of_watches(data):
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Number of Watches Sold'], label="Watches Sold", marker='o')
    plt.plot(data.index, data['Number of Watches Added'], label="Watches Added", marker='o')
    plt.xlabel('Date')
    plt.ylabel('Number of Watches')
    plt.title('Watches Sold and Added Over Time')
    plt.legend()
    st.pyplot(plt)

# Watch data visualizations
def plot_price_evolution(data):
    brands = data['Brand'].unique()
    selected_brand = st.selectbox('Select Brand', brands)
    
    models = data[data['Brand'] == selected_brand]['Model'].unique()
    selected_model = st.selectbox('Select Model', models)
    
    filtered_data = data[(data['Brand'] == selected_brand) & (data['Model'] == selected_model)]
    
    plt.figure(figsize=(10, 5))
    for _, row in filtered_data.iterrows():
        price_history = pd.DataFrame(row['PriceHistory'])
        
        # Convert "sold" to NaN and drop those rows
        price_history['Price'] = pd.to_numeric(price_history['Price'], errors='coerce')
        price_history.dropna(subset=['Price'], inplace=True)
        
        # Plot the cleaned price history
        plt.plot(pd.to_datetime(price_history['Date']), price_history['Price'], label=row['Title'])
    
    #plt.title(f"Price Evolution: {selected_brand} {selected_model}")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    #plt.legend()
    st.pyplot(plt)


def plot_price_distribution(data):
    brands = data['Brand'].unique()
    selected_brand = st.selectbox('Select Brand', brands)
    
    years = data[data['Brand'] == selected_brand]['Year'].dropna().unique()
    selected_year = st.selectbox('Select Year', years)
    
    filtered_data = data[(data['Brand'] == selected_brand) & (data['Year'] == selected_year)]
    
    final_prices = []
    for _, row in filtered_data.iterrows():
        price_history = row['PriceHistory']
        final_price = price_history[-1]['Price'] if price_history[-1]['Price'] != 'sold' else price_history[-2]['Price']
        final_prices.append(final_price)
    
    plt.figure(figsize=(10, 5))
    plt.hist(final_prices, bins=20)
    plt.title(f"Price Distribution: {selected_brand} in {selected_year}")
    plt.xlabel("Price (USD)")
    plt.ylabel("Number of Watches")
    st.pyplot(plt)

def plot_time_to_sell(data):
    time_to_sell = []
    
    for _, row in data.iterrows():
        price_history = row['PriceHistory']
        if price_history[-1]['Price'] == 'sold':
            start_date = pd.to_datetime(price_history[0]['Date'])
            sold_date = pd.to_datetime(price_history[-1]['Date'])
            days_to_sell = (sold_date - start_date).days
            time_to_sell.append(days_to_sell)
    
    plt.figure(figsize=(10, 5))
    plt.hist(time_to_sell, bins=20)
    plt.title("Distribution of Time to Sell (Days)")
    plt.xlabel("Days to Sell")
    plt.ylabel("Number of Watches")
    st.pyplot(plt)

def plot_top_brands(data):
    selected_year = st.selectbox('Select Year', data['Year'].dropna().unique())
    
    filtered_data = data[data['Year'] == selected_year]
    
    brand_sales = filtered_data['Brand'].value_counts()
    
    plt.figure(figsize=(10, 5))
    brand_sales.plot(kind='bar')
    plt.title(f"Top Selling Brands in {selected_year}")
    plt.xlabel("Brand")
    plt.ylabel("Number of Watches Sold")
    st.pyplot(plt)

def plot_price_comparison(data):
    plt.figure(figsize=(10, 5))
    data['FinalPrice'] = data['PriceHistory'].apply(lambda x: x[-2]['Price'] if x[-1]['Price'] == 'sold' else x[-1]['Price'])
    sns.boxplot(x='Brand', y='FinalPrice', data=data)
    plt.title("Price Comparison Across Brands")
    plt.xlabel("Brand")
    plt.ylabel("Final Price (USD)")
    st.pyplot(plt)

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
        
        # Watch Visualizations
        analysis_type = st.sidebar.selectbox("Select Analysis Type", 
                                             ["Price Evolution", "Price Distribution", "Time to Sell", "Top Brands", "Price Comparison"])
        
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
