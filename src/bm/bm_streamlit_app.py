# Import necessary libraries
import pandas as pd
import streamlit as st

# Title and description for the Streamlit dashboard
st.title('Burning Man Camp Dues Analysis')
st.write('An interactive dashboard for analyzing camp dues and financial policies of Burning Man theme camps.')

# Upload CSV file
uploaded_file = st.file_uploader("Upload your survey data CSV", type=['csv'])

if uploaded_file:
    # Read the CSV file using pandas
    df = pd.read_csv(uploaded_file)

    # Display the first few rows of the data
    st.write('### Survey Data Overview')
    st.dataframe(df.head())

    # Provide some key statistics and data filtering options
    st.write('### Summary Statistics')
    camp_size_min = st.slider('Minimum Camp Size', 0, int(df['Camp Size'].max()), 0)
    camp_size_max = st.slider('Maximum Camp Size', 0, int(df['Camp Size'].max()), int(df['Camp Size'].max()))
    df_filtered = df[(df['Camp Size'] >= camp_size_min) & (df['Camp Size'] <= camp_size_max)]

    st.write(f'Displaying data for camps with sizes between {camp_size_min} and {camp_size_max}.')
    st.dataframe(df_filtered)

    # Calculate and display aggregated metrics
    total_camps = len(df_filtered)
    avg_contrib = df_filtered['Average Per Person Camp Contribution'].mean()
    total_budget = df_filtered['Camp Total Annual Budget'].sum()

    st.write(f'**Total Camps Analyzed:** {total_camps}')
    st.write(f'**Average Per Person Contribution:** {avg_contrib:.2f}')
    st.write(f'**Total Annual Budget Across Camps:** {total_budget:.2f}')

    # Visualizations to help answer the business questions
    st.write('### Visualization')
    selected_metric = st.selectbox('Choose a metric to plot', ['Camp Size', 'Average Per Person Camp Contribution', 'Camp Total Annual Budget'])

    # Generate and show plots
    st.write(f'#### Distribution of {selected_metric}')
    st.bar_chart(df_filtered[selected_metric])

    # Analyze contribution structures
    st.write('### Contribution Structures')
    contribution_structure = df_filtered['How are camp contributions structured?'].value_counts()
    st.write(contribution_structure)

    # Other analyses can be added based on the specific business questions

else:
    st.write('Please upload your survey data CSV to proceed.')
