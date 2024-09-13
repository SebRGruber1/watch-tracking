import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load the data
@st.cache_data
def load_data():
    return pd.read_json("portfolio_statistics.json")

# Preprocessing
def preprocess_data(data):
    # Since data seems to be nested under dates, let's reset the index and flatten the data
    data = pd.DataFrame(data).T  # Transpose the data so dates become rows

    # Replace $ and , in the values and convert to float
    for col in ["Total Value of Watches For Sale", "Total Value of Watches Sold", "Total Value of Watches Added"]:
        if col in data.columns:
            data[col] = data[col].replace({'\$': '', ',': ''}, regex=True).astype(float)
        else:
            st.write(f"Column '{col}' not found in the dataset.")  # Alert if a column is missing

    return data

# Plot total value of watches for sale
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

# Visualize the number of watches sold and added
def plot_number_of_watches(data):
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Number of Watches Sold'], label="Watches Sold", marker='o')
    plt.plot(data.index, data['Number of Watches Added'], label="Watches Added", marker='o')
    plt.xlabel('Date')
    plt.ylabel('Number of Watches')
    plt.title('Watches Sold and Added Over Time')
    plt.legend()
    st.pyplot(plt)

# Streamlit App Layout
def main():
    st.title("Watch Data Visual Analysis")

    data = load_data()
    data = preprocess_data(data)

    # Display raw data
    if st.checkbox('Show Raw Data'):
        st.write(data)

    # Visualization 1: Total Value of Watches Over Time
    st.subheader("Total Value of Watches Over Time")
    plot_total_value(data)

    # Visualization 2: Watches Sold and Added Over Time
    st.subheader("Watches Sold and Added Over Time")
    plot_number_of_watches(data)

if __name__ == "__main__":
    main()
