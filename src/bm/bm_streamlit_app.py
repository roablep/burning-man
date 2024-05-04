# streamlit run /Users/peter/github/burning-man/src/bm/bm_streamlit_app.py

# Import necessary libraries
import pandas as pd
import streamlit as st
import altair as alt
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

matplotlib.use('TkAgg')
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
camp_size = st.sidebar.slider("Select Camp Size", min_size, max_size, (min_size, max_size))
filtered_df = df[(df['Camp Size'] >= camp_size[0]) & (df['Camp Size'] <= camp_size[1])]

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
st.write(f'**Average Per Person Contribution:** {avg_contrib:.2f}')
st.write(f'**Average Annual Budget Across Camps:** {total_budget:.2f}')

# QUESTION: Distribution of Camp Sizes
st.subheader("Distribution of Camp Sizes")
camp_size_hist = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X('Camp Size', bin=alt.Bin(maxbins=10), title="Camp Size"),
    y=alt.Y('count()', title='Number of Camps')
)
st.altair_chart(camp_size_hist, use_container_width=True)

# QUESTION: Distribution of Average Camp Dues
st.subheader("Distribution of Average Per Person Camp Contribution")
average_dues_hist = alt.Chart(filtered_df[filtered_df['Average Per Person Camp Contribution'].notna()]).mark_bar().encode(
    x=alt.X('Average Per Person Camp Contribution', bin=alt.Bin(maxbins=10), title="Average Contribution Per Person"),
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


# QUESTION: How close is the average camper contribution relative to the max/min?
# Error bars of high/mid/low by camp size. 
df2 = filtered_df[filtered_df['Error Lower'].notnull() & filtered_df['Error Upper'].notnull()]
st.title("Contribution Ranges and Average Contribution vs. Camp Size")
# fig, ax = plt.subplots(figsize=(12, 8))

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
st.pyplot(plt)

error_bars = alt.Chart(df2).mark_errorbar(extent='ci').encode(
    x=alt.X('Camp Size:Q', title='Camp Size'),
    y=alt.Y('Average Per Person Camp Contribution:Q', title='Average Contribution Per Person'),
    yError='Error Upper:Q',
    yError2='Error Lower:Q',
    tooltip=['Camp Size', 'Average Per Person Camp Contribution']
)

# Base scatter plot to add markers on the error bars
base = alt.Chart(df2).mark_point().encode(
    x='Camp Size:Q',
    y='Average Per Person Camp Contribution:Q',
    tooltip=['Camp Size', 'Average Per Person Camp Contribution']
)

# Combine the error bars and base markers
chart = (error_bars + base).interactive()
st.altair_chart(chart, use_container_width=True)

# QUESTION: How do camp fees vary based on amenities offered?
st.write("Filtering will not work for anything below here.")
df_melted = df[df['Average Per Person Camp Contribution'].notnull()].melt(id_vars=['ndx', 'Average Per Person Camp Contribution'], value_vars=amenity_columns, var_name='Amenity', value_name='Presence')
# grouped_data = df_melted.groupby(['Amenity','Presence'])['Average Per Person Camp Contribution'].describe(percentiles=[.25, .5, .75])
df_melted2 = df_melted[df_melted['Presence'] == 1]

boxplot = alt.Chart(df_melted2).mark_boxplot(size=30).encode(
    x=alt.X('Amenity:N', title='Amenity', sort=list(df_binarized.columns)),
    y=alt.Y('Average Per Person Camp Contribution:Q', title='Average Contribution Per Person'),
    tooltip=['ndx', 'Average Per Person Camp Contribution']
).properties(
    title='Average Contribution vs. Presence of Amenities',
    width=700,
    height=400
).configure_axisX(labelAngle=-45)
st.altair_chart(boxplot, use_container_width=True)


# Now let's do the same avg camper dues boxplot but account for yes/no of each amenity offered
#g = sns.FacetGrid(df_melted, col='Amenity', col_wrap=3, height=4)  # Adjust col_wrap for the number of amenities 
#g.map(sns.boxplot, 'Presence', 'Average Per Person Camp Contribution', showmeans=True)
#plt.savefig('/Users/peter/Downloads/contribution_vs_amenities_boxplot.png')

boxplot_subplot = alt.Chart(df_melted).mark_boxplot().encode(
    x=alt.X('Presence:O', title='Amenity is Present'),  # Labels for amenity presence/absence
    y=alt.Y('Average Per Person Camp Contribution:Q', title='Average Contribution Per Person'),
    column=alt.Column('Amenity:N', title=None)  # Split by amenity type
).properties(
    width=150,  # Adjust column width
).configure_axisX(labelAngle=-45)
st.altair_chart(boxplot_subplot, use_container_width=True)

# Let's run a regression. 
features = amenity_columns

model_source_df = df[features+['Average Per Person Camp Contribution']].dropna()
X = model_source_df[features + ['benefactor']].astype(int)
y = model_source_df['Average Per Person Camp Contribution']

assert X.dtypes.all() in ['int64', 'float64'], "Check X for non-numeric values."
assert y.dtype in ['int64', 'float64'], "Check y for non-numeric values."

X = sm.add_constant(X)
model = sm.OLS(y, X).fit()
print(model.summary())

st.title("Regression Analysis: Average Per Person Camp Contribution")


# Display regression summary
st.subheader("Regression Model Summary")
st.text(model.summary())

#from sklearn.model_selection import train_test_split
#from sklearn.linear_model import LinearRegression
#from sklearn.metrics import r2_score 
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42) 
# # Create and fit the model
# model = LinearRegression()
# model.fit(X, y) 
# y_pred = model.predict(X_test) 
# r2 = r2_score(y_test, y_pred)
# print('R-squared:', r2) 
# print('Coefficients:', model.coef_) 

# Now let's visualize the feature importance
# Extract coefficients from the model
coef = model.params
features = coef.index
# Plot the coefficients
# plt.figure(figsize=(10, 6))
# plt.barh(features, coef)
# plt.xlabel('Coefficient Value')
# plt.ylabel('Feature')
# plt.title('Regression Coefficients')
# plt.grid(axis='x', linestyle='--', linewidth=0.5)
# plt.show()
# Prepare the data for Altair
coef_data = pd.DataFrame({
    'Feature': features,
    'Coefficient Value': coef
}).reset_index(drop=True)

# Create an Altair bar chart to visualize coefficients
coef_chart = alt.Chart(coef_data).mark_bar().encode(
    y=alt.Y('Feature:N', sort='-x', title='Feature'),
    x=alt.X('Coefficient Value:Q', title='Coefficient Value'),
    tooltip=['Feature', 'Coefficient Value']
).properties(
    title='Regression Coefficients',
    width=700,
    height=400
).configure_axis(grid=True)

# Streamlit layout
st.title("Regression Analysis: Feature Importance")
st.write("This visualization shows the coefficient values for each feature used in the regression analysis.")

st.altair_chart(coef_chart, use_container_width=True)


st.write("What did we learn? I guess we learned not to do it again. This model doesn't seem to have much explanatory power. No way in hell does including booze, greywater, and water as camp amenities make dues CHEAPER.\nThere may be a relationship we're not directly seeing because it's not in the survey, like a correlation between these amenetities and a benevolent benefactor/sugar mommy/daddy.\n")

st.write("So let's do another model *with* an indicator of if the camp has that sugar mommy/daddy\nI implied the presence of a benefactor by looking at the difference between the average dues and upper end of dues for camps that operated on a sliding scale rather than flat fee. Camps which had upper dues greater than 1x the average dues There were only 31 camps (35%) so take this with a grain of salt since not much data to work with.")

# Add some rough indicators if there is an especially rich member
sugar_df = df[df['rng_to_avg'].notnull()]
sugar_df['benefactor'] = 0
sugar_df.loc[(sugar_df['Tidbits'].notnull() & sugar_df['Tidbits'].str.contains('benefactor')), 'benefactor'] = 1
sugar_df.loc[sugar_df['rng_to_avg'] > 1, 'benefactor'] = 1


model_source_df = sugar_df[features+['Average Per Person Camp Contribution', 'benefactor']].dropna()
X = model_source_df[features + ['benefactor']].astype(int)
y = model_source_df['Average Per Person Camp Contribution']

assert X.dtypes.all() in ['int64', 'float64'], "Check X for non-numeric values."
assert y.dtype in ['int64', 'float64'], "Check y for non-numeric values."

X = sm.add_constant(X)
model2 = sm.OLS(y, X).fit()
print(model2.summary())

# Display regression summary
st.subheader("Regression Model Summary: Average Per Person Camp Contribution among camps with that special Sugar Daddy/Mommy")
st.text(model.summary())

st.write("What did we learn? Camps with a sugar mommy/daddy pay more! But again, small sample so let's shrug and say YOLO.")

# import seaborn as sns
# plt.figure(figsize=(14, 8))
# sns.boxplot(x='Amenity', y='Average Per Person Camp Contribution', data=df_melted)
# plt.title('Average Contribution vs. Presence of Amenities')
# plt.xlabel('Amenity')
# plt.ylabel('Average Per Person Contribution')
# plt.xticks(rotation=45, ha='right')
# plt.grid(visible=True, axis='y', linestyle='--', linewidth=0.5)
# plt.savefig('/Users/peter/Downloads/contribution_vs_amenities_boxplot.png')

# Analyze contribution structures
st.write('### Contribution Structures')
contribution_structure = filtered_df['How are camp contributions structured?'].value_counts()
st.write(contribution_structure)


# RSR mentions basd on size , budget

