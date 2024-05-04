# Import necessary libraries
import pandas as pd
import streamlit as st
import altair as alt
import matplotlib
import matplotlib.pyplot as plt
import statsmodels.api as sm

matplotlib.use('TkAgg')
# matplotlib.use('nbAgg')

alt.renderers.enable('browser')

df = pd.read_csv("/Users/peter/Downloads/Theme Camp Dues!.csv")

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


print(df.describe())

# How many camps are in the survey? 
print(len(df))

# How many camps are in the survey where we have decent data?
len(df[df['Average Per Person Camp Contribution'].notna() & len(df['Camp Size'].notna())] ) 

# What is the distribution of camp sizes?
plt.figure(figsize=(8, 5)) 
plt.hist(df['Camp Size'])
plt.xlabel('Camp Size')
plt.ylabel('Number of Camps')
plt.title('Distribution of Camp Sizes')
plt.show()

plt.figure(figsize=(10, 6))
plt.hist(df['Camp Size'], bins=10, edgecolor='black')
plt.title('Distribution of Camp Size')
plt.xlabel('Camp Size')
plt.ylabel('Frequency')
plt.grid(axis='y')
plt.show()


# Altair - Average Contribution vs. Camp Size
data1 = df[['Camp Size', 'Average Per Person Camp Contribution']]
chart = alt.Chart(data1).mark_circle(size=60).encode(
    x=alt.X('Camp Size', title='Camp Size'),
    y=alt.Y('Average Per Person Camp Contribution', title='Average Contribution Per Person'),
    tooltip=['Camp Size', 'Average Per Person Camp Contribution']
).interactive().properties(
    title='Average Contribution Per Person vs. Camp Size',
    width=600,
    height=400
)
chart.display()
# st.altair_chart(chart)

# How close is the average camper contribution relative to the max/min?
# Error bars of high/mid/low by camp size. 
df2 = df[df['Error Lower'].notnull() & df['Error Upper'].notnull()]
plt.figure(figsize=(12, 8))

plt.errorbar(df2['Camp Size'], df2['Average Per Person Camp Contribution'],
             yerr=[df2['Error Lower'], df2['Error Upper']],
             # fmt='o', 
             ecolor='red', capsize=5, elinewidth=2, marker='s', markersize=7)


# Customize the plot
plt.title('Contribution Ranges and Average Contribution vs. Camp Size')
plt.xlabel('Camp Size')
plt.ylabel('Average Contribution Per Person')
plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5)
plt.savefig('/Users/peter/Downloads/contribution_errorbars_vs_camp_size.png')
# st.pyplot(plt)

# QUESTION: How do camp fees vary based on amenities offered?
df_melted = df[df['Average Per Person Camp Contribution'].notnull()].melt(id_vars=['ndx', 'Average Per Person Camp Contribution'], value_vars=amenity_columns,
                          var_name='Amenity', value_name='Presence')
df_melted = df_melted[df_melted['Presence'] == 1]


chart = alt.Chart(df_melted).mark_boxplot(size=30).encode(
    x=alt.X('Amenity:N', title='Amenity', sort=list(df_binarized.columns)),
    y=alt.Y('Average Per Person Camp Contribution:Q', title='Average Contribution Per Person'),
    tooltip=['ndx', 'Average Per Person Camp Contribution']
).properties(
    title='Average Contribution vs. Presence of Amenities',
    width=700,
    height=400
).configure_axisX(labelAngle=-45)
chart.display()


# Let's run a regression. 
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score 
features = amenity_columns
df['benefactor'] = 0
df.loc[(df['Tidbits'].notnull() & df['Tidbits'].str.contains('benefactor')), 'benefactor'] = 1
df.loc[df['rng_to_avg'] > 1, 'benefactor'] = 1

model_source_df = df[features+['Average Per Person Camp Contribution', 'benefactor']].dropna()
X = model_source_df[features + ['benefactor']].astype(int)
y = model_source_df['Average Per Person Camp Contribution']

assert X.dtypes.all() in ['int64', 'float64'], "Check X for non-numeric values."
assert y.dtype in ['int64', 'float64'], "Check y for non-numeric values."

# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42) 
# # Create and fit the model
# model = LinearRegression()
# model.fit(X, y) 
# y_pred = model.predict(X_test) 
# r2 = r2_score(y_test, y_pred)
# print('R-squared:', r2) 
# print('Coefficients:', model.coef_) 


X = sm.add_constant(X)
model = sm.OLS(y, X).fit()
print(model.summary())
# What did we learn? I guess we learned not to do it again. This model very clearly has little explanatory power. No way in hell does including booze, greywater, and water as camp amenities make dues CHEAPER. There may be a relationship we're not directly seeing because it's not in the survey, like a correlation between these amenetities and a benevolent benefactor/sugar mommy/daddy. 
# I implied the presence of a benefactor by looking at the difference between the average dues and upper end of dues for camps that operated on a sliding scale rather than flat fee. Camps which had upper dues greater than 1x the average dues There were only 31 camps (35%) so take this with a grain of salt since not much data to work with. 
# There are ways to peek at it but I don't feel like spending more time trying to get more explanatory power out of the model. Let's shrug and say YOLO.




# import seaborn as sns
# plt.figure(figsize=(14, 8))
# sns.boxplot(x='Amenity', y='Average Per Person Camp Contribution', data=df_melted)
# plt.title('Average Contribution vs. Presence of Amenities')
# plt.xlabel('Amenity')
# plt.ylabel('Average Per Person Contribution')
# plt.xticks(rotation=45, ha='right')
# plt.grid(visible=True, axis='y', linestyle='--', linewidth=0.5)
# plt.savefig('/Users/peter/Downloads/contribution_vs_amenities_boxplot.png')


# Grouped by camp size? Count of Amenities
# RSR mentions basd on size , budget




# Title and description for the Streamlit dashboard
st.title('Burning Man Camp Dues Analysis')
st.write('An interactive dashboard for analyzing camp dues and financial policies of Burning Man theme camps.')



### Data cleaning
encoded_df = pd.get_dummies(df, columns=['How are camp contributions structured?','Camp Amenities'])


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

# Plot 1: Distribution of Camp Sizes
chart1 = alt.Chart(df_filtered).mark_bar().encode(
    x=alt.X('Camp Size', bin=True, title='Camp Size (Binned)'),
    y=alt.Y('count()', title='Number of Camps')
).properties(
    title='Distribution of Camp Sizes',
    width=600,
    height=400
)
st.altair_chart(chart1, use_container_width=True)

# Plot 2: Average Per Person Contribution vs. Camp Size
chart2 = alt.Chart(df_filtered).mark_circle(size=60).encode(
    x=alt.X('Camp Size', title='Camp Size'),
    y=alt.Y('Average Per Person Camp Contribution', title='Average Contribution Per Person'),
    tooltip=['Camp Name', 'Camp Size', 'Average Per Person Camp Contribution']
).interactive().properties(
    title='Average Contribution Per Person vs. Camp Size',
    width=600,
    height=400
)
st.altair_chart(chart2, use_container_width=True)

# Sample bar chart showing the count of different amenities 
amenities_chart = alt.Chart(df).mark_bar().encode(
    x='count()',
    y='Camp Amenities'
)

st.altair_chart(amenities_chart, use_container_width=True) 

# Calculate average camp dues
average_dues = df['Average Per Person Camp Contribution'].mean()

# Display the result
st.header("Average Camp Dues")
st.metric("Average", f"${average_dues:.2f}") 

plt.figure(figsize=(8, 5))  # Adjust figure size as needed 
plt.scatter(data['Camp Size'], data['Average Per Person Camp Contribution'])
plt.xlabel('Camp Size')
plt.ylabel('Average Camp Contribution')
plt.title('Camp Size vs. Average Camp Contribution')

# Display the plot in Streamlit
st.pyplot(plt)


