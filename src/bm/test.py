# streamlit run /Users/peter/github/burning-man/src/bm/bm_streamlit_app.py

# Import necessary libraries
import pandas as pd
import streamlit as st
import altair as alt
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

# matplotlib.use('TkAgg')
# matplotlib.use('nbAgg')

alt.renderers.enable('browser')

df = pd.read_csv("/Users/peter/Downloads/Theme Camp Dues!.csv")
df.drop('Camp Name', axis=1, inplace=True)

df['ndx'] = df.index
df['Camp Size'] = pd.to_numeric(df['Camp Size'])
df['Average Per Person Camp Contribution'] = pd.to_numeric(df['Average Per Person Camp Contribution'].replace({'\$': '', ',': ''}, regex=True))
df['Camp Total Annual Budget'] = pd.to_numeric(df['Camp Total Annual Budget'].replace({'\$': '', ',': ''}, regex=True))

df['budget_pp'] = df['Camp Total Annual Budget']/df['Camp Size']*1.0
df['budget_variance'] = df['Average Per Person Camp Contribution']/df['budget_pp']-1

def calculate_avg_position(df):
    df['ContributionRangeLow'] = pd.to_numeric(df['ContributionRangeLow'])
    df['ContributionRangeHigh'] = pd.to_numeric(df['ContributionRangeHigh'])

    df['Error Lower'] = df['Average Per Person Camp Contribution'] - df['ContributionRangeLow']
    df['Error Upper'] = df['ContributionRangeHigh'] - df['Average Per Person Camp Contribution']

    df['ContributionRange'] = df['ContributionRangeHigh'] - df['ContributionRangeLow']
    df['Difference from Min'] = df['Average Per Person Camp Contribution'] - df['ContributionRangeLow']
    df['Difference from Max'] = df['ContributionRangeHigh'] - df['Average Per Person Camp Contribution']
    df['Percent Difference from Min'] = (df['Difference from Min'] / df['ContributionRange']) * 100
    df['Percent Difference from Max'] = (df['Difference from Max'] / df['ContributionRange']) * 100
    df['AvgRelativePosition'] = (df['Average Per Person Camp Contribution'] - df['ContributionRangeLow']) / df['ContributionRange']
    
    df['avg_to_max_pct'] = df['Average Per Person Camp Contribution'] / df['ContributionRangeHigh'] 
    df['rng_to_avg'] = df['Difference from Max'] / df['Average Per Person Camp Contribution']  # may imply a camp benefactor
    return df

df = calculate_avg_position(df)

# df['Camp Amenities'].str.strip().str.split(';', expand=True)
df['Camp Amenities'] = [x for x in df['Camp Amenities'].str.split(';') if x != '']
df_exploded = df.explode('Camp Amenities')
df_exploded['Camp Amenities'] = df_exploded['Camp Amenities'].str.strip()
# Use pandas' get_dummies function to create the binary columns
df_dummies = pd.get_dummies(df_exploded['Camp Amenities'])
# Group by 'Camp Name' to aggregate multiple rows for the same camp
# Sum across each group since the one-hot encoding has binary values (0 or 1)
df_binarized = df_dummies.groupby(df_exploded['ndx']).max()
amenity_columns = [col for col in df_binarized.columns if df_binarized[col].sum() > 0]
df = df.join(df_binarized)


st.title("Theme Camp Dues Analysis Dashboard")
st.sidebar.header("Filter Options")

# Camp Size Filter
min_size, max_size = int(df['Camp Size'].min()), int(df['Camp Size'].max())
camp_size = st.sidebar.slider("Camp Size", min_size, max_size, (min_size, max_size))

min_dues, max_dues = int(df['Average Per Person Camp Contribution'].min()), int(df['Average Per Person Camp Contribution'].max())
camp_dues = st.sidebar.slider("Avg $/per person Dues", min_dues, max_dues, (min_dues, max_dues))

filtered_df = df[(df['Camp Size'] >= camp_size[0]) & (df['Camp Size'] <= camp_size[1]) & (df['Average Per Person Camp Contribution'] >= camp_dues[0]) & (df['Average Per Person Camp Contribution'] <= camp_dues[1])]

# Amenities Filter
selected_amenities = st.sidebar.multiselect("Select Amenities", amenity_columns)
if selected_amenities:
    for amenity in selected_amenities:
        filtered_df = filtered_df[filtered_df[amenity] == 1]

# QUESTION: How many camps are in the survey? 
total_camps = len(df)

# QUESTION: How many camps are in the survey where we have decent data?
camps_with_data = len(df[df['Average Per Person Camp Contribution'].notna() & df['Camp Size'].notna()])

avg_contrib = df['Average Per Person Camp Contribution'].mean()
total_budget = df['Camp Total Annual Budget'].mean()

st.write(f"**Total Number of Camps in the Survey:** {total_camps}")
st.write(f"**Camps with Complete Data:** {camps_with_data}")
st.write(f'**Average Per Person Contribution:** ${avg_contrib:,.0f}')
st.write(f'**Average Annual Budget Across Camps:** ${total_budget:,.0f}')

st.subheader("Distribution of Camp Sizes")
camp_size_hist = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X('Camp Size', bin=alt.Bin(maxbins=50), title="Camp Size"),
    y=alt.Y('count()', title='Number of Camps')
)
st.altair_chart(camp_size_hist, use_container_width=True)

# QUESTION: Distribution of Average Camp Dues
st.subheader("Distribution of Average Per Person Camp Contribution")
average_dues_hist = alt.Chart(filtered_df[filtered_df['Average Per Person Camp Contribution'].notna()]).mark_bar().encode(
    x=alt.X('Average Per Person Camp Contribution', bin=alt.Bin(maxbins=50), title="$ per person"),
    y=alt.Y('count()', title='Number of Camps')
)
st.altair_chart(average_dues_hist, use_container_width=True)

# QUESTION: Average Contribution vs. Camp Size
data1 = filtered_df[['Camp Size', 'Average Per Person Camp Contribution']]
chart1 = alt.Chart(data1).mark_circle(size=60).encode(
    x=alt.X('Camp Size', title='Camp Size'),
    y=alt.Y('Average Per Person Camp Contribution', title='Average Contribution Per Person'),
    tooltip=['Camp Size', 'Average Per Person Camp Contribution']
).interactive().properties(
    title='Average Contribution Per Person vs. Camp Size',
    width=600,
    height=400
)
st.altair_chart(chart1, use_container_width=True)

df2 = filtered_df[filtered_df['Error Lower'].notnull() & filtered_df['Error Upper'].notnull()]
st.title("Contribution Ranges and Average Contribution vs. Camp Size")

#create your figure and get the figure object returned
fig = plt.figure() 


plt.figure(figsize=(12, 8))  # Set the figure size
plt.errorbar(df_clean['Camp Size'], df_clean['Average Per Person Camp Contribution'],
             yerr=[df_clean['Error Lower'], df_clean['Error Upper']],
             fmt='o', ecolor='red', capsize=5, elinewidth=2, marker='s', markersize=7)  # Create error bars


plt.figure(figsize=(12, 8))
plt.errorbar(df_clean['Camp Size'], df_clean['Average Per Person Camp Contribution'],
             yerr=[df_clean['Error Lower'], df_clean['Error Upper']],
             fmt='o', ecolor='red', capsize=5, elinewidth=2, marker='s', markersize=7)
plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5)
