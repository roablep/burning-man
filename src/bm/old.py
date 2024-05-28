# streamlit run /Users/peter/github/burning-man/src/bm/bm_streamlit_app.py

# Import necessary libraries
import pandas as pd
import streamlit as st
import altair as alt
import matplotlib
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import statsmodels.api as sm

# matplotlib.use('TkAgg')  # this will crash streamlit
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

df['implied_budget']=df['Camp Size']*df['Average Per Person Camp Contribution']
df['validation_difference'] = (df['implied_budget']/df['Camp Total Annual Budget']*1.0 - 1)*100

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
df_binarized_amenity = df_dummies.groupby(df_exploded['ndx']).max()
amenity_columns = [col for col in df_binarized_amenity.columns if df_binarized_amenity[col].sum() > 0]
df = df.join(df_binarized_amenity)


df['How are camp contributions structured?'] = [x for x in df['How are camp contributions structured?'].str.split(';') if x != '']
df_exploded = df.explode('How are camp contributions structured?')
df_exploded['How are camp contributions structured?'] = df_exploded['How are camp contributions structured?'].str.strip()
# Use pandas' get_dummies function to create the binary columns
df_dummies = pd.get_dummies(df_exploded['How are camp contributions structured?'])
# Group by 'Camp Name' to aggregate multiple rows for the same camp
# Sum across each group since the one-hot encoding has binary values (0 or 1)
df_binarized_fee = df_dummies.groupby(df_exploded['ndx']).max()
fee_columns = [col for col in df_binarized_fee.columns if df_binarized_fee[col].sum() > 0]
df = df.join(df_binarized_fee)

df['Do supplemental contributions support other camp amenities (in addition to core contribution)'] = [x for x in df['Do supplemental contributions support other camp amenities (in addition to core contribution)'].str.split(';') if x != '']
df['Do supplemental contributions support other camp amenities (in addition to core contribution)'] = df['Do supplemental contributions support other camp amenities (in addition to core contribution)'].apply(lambda x: [item.strip() for item in x] if isinstance(x, list) else x)
df['has_extra_paid_in_amenities'] = df['Do supplemental contributions support other camp amenities (in addition to core contribution)'].notna()


st.title("Theme Camp Dues Survey Results")
st.sidebar.header("Filter Options")

# Camp Size Filter
min_size, max_size = int(df['Camp Size'].min()), int(df['Camp Size'].max())
camp_size = st.sidebar.slider("Camp Size", min_size, max_size, (min_size, max_size))

min_dues, max_dues = int(df['Average Per Person Camp Contribution'].min()), int(df['Average Per Person Camp Contribution'].max())
camp_dues = st.sidebar.slider("Avg $/per person Dues", min_dues, max_dues, (min_dues, max_dues))

filtered_df = df[(df['Camp Size'] >= camp_size[0]) & (df['Camp Size'] <= camp_size[1]) & (df['Average Per Person Camp Contribution'] >= camp_dues[0]) & (df['Average Per Person Camp Contribution'] <= camp_dues[1])]
filtered_df.drop(axis=1, columns=['Tidbits', 'Commentary'], inplace=True)

# Amenities Filter
selected_amenities = st.sidebar.multiselect("Select Amenities", amenity_columns)
if selected_amenities:
    for amenity in selected_amenities:
        filtered_df = filtered_df[filtered_df[amenity] == 1]

# QUESTION: How many camps are in the survey? 
total_camps = len(df)

# QUESTION: How many camps are in the survey where we have decent data?
camps_with_data = len(df[df['Average Per Person Camp Contribution'].notna() & df['Camp Size'].notna()])

# Calculate mean and median
mean_dues = df['Average Per Person Camp Contribution'].mean()
median_dues = df['Average Per Person Camp Contribution'].median()
mean_size = df['Camp Size'].mean()
median_size = df['Camp Size'].median()
mean_budget = filtered_df['Camp Total Annual Budget'].mean()
median_budget = filtered_df['Camp Total Annual Budget'].median()

st.write(f"## Summary Stats ##")

st.write(f"**Total Number of Camps in the Survey:** {total_camps}")
st.write(f"**Camps with Complete Data:** {camps_with_data}")
st.write(f'**Average Camp Size:** {mean_size:,.0f}')
st.write(f'**Average Dues:** ${mean_dues:,.0f}')
st.write(f'**Average Annual Budget:** ${mean_budget:,.0f}')

camp_size_hist = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X('Camp Size', bin=alt.Bin(maxbins=50), title="Camp Size"),
    y=alt.Y('count()', title='Number of Camps')
).interactive().properties(
    title='Camp Size Distribution',
    width=600,
    height=400
)
mean_line_size = alt.Chart(pd.DataFrame({'x': [mean_size]})).mark_rule(color='red').encode(
    x=alt.X('x', title='Mean'),
    tooltip=[alt.Tooltip('x', title='Mean Size')]
)

median_line_size = alt.Chart(pd.DataFrame({'x': [median_size]})).mark_rule(color='blue').encode(
    x=alt.X('x', title='Median'),
    tooltip=[alt.Tooltip('x', title='Median Size')]
)
st.altair_chart(camp_size_hist + mean_line_size + median_line_size, use_container_width=True)

# QUESTION: Distribution of Average Camp Dues
average_dues_hist = alt.Chart(filtered_df[filtered_df['Average Per Person Camp Contribution'].notna()]).mark_bar().encode(
    x=alt.X('Average Per Person Camp Contribution', bin=alt.Bin(maxbins=50), title="$ per person"),
    y=alt.Y('count()', title='Number of Camps')
).interactive().properties(
    title='Average Per Person Camp Contribution Distribution',
    width=600,
    height=400
)
dues_mean_line_dues = alt.Chart(pd.DataFrame({'x': [mean_dues]})).mark_rule(color='red').encode(
    x=alt.X('x', title='Mean'),
    tooltip=[alt.Tooltip('x', title='Mean Dues')]
)

dues_median_line_dues = alt.Chart(pd.DataFrame({'x': [median_dues]})).mark_rule(color='blue').encode(
    x=alt.X('x', title='Median'),
    tooltip=[alt.Tooltip('x', title='Median Dues')]
)
st.altair_chart(average_dues_hist + dues_mean_line_dues + dues_median_line_dues, use_container_width=True)

total_budget_hist = alt.Chart(filtered_df[filtered_df['Camp Total Annual Budget'].notna()]).mark_bar().encode(
    x=alt.X('Camp Total Annual Budget', bin=alt.Bin(maxbins=50), title="Total Annual Budget ($)"),
    y=alt.Y('count()', title='Number of Camps')
).properties(
    title='Total Annual Budget Distribution',
    width=600,
    height=400
).interactive()
mean_line_budget = alt.Chart(pd.DataFrame({'x': [mean_budget]})).mark_rule(color='red').encode(
    x=alt.X('x', title='Mean'),
    tooltip=[alt.Tooltip('x', title='Mean Budget')]
)
median_line_budget = alt.Chart(pd.DataFrame({'x': [median_budget]})).mark_rule(color='blue').encode(
    x=alt.X('x', title='Median'),
    tooltip=[alt.Tooltip('x', title='Median Budget')]
)
st.altair_chart(total_budget_hist + mean_line_budget + median_line_budget, use_container_width=True)

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

st.write("## Drilling into Financial Structures")

st.write("First, let's look camp contribution models.")
exploded_fee = filtered_df['How are camp contributions structured?'].dropna().explode('How are camp contributions structured?').reset_index(drop=True)
# Count the occurrences of each contribution type
fee_counts = exploded_fee.value_counts().reset_index()
fee_counts.columns = ['Contribution Type', 'Count']
fee_counts['Percentage'] = (fee_counts['Count'] / fee_counts['Count'].sum())
fee_counts = fee_counts.sort_values(by='Count', ascending=True)

fee_counts_chart = alt.Chart(fee_counts).mark_arc().encode(
    theta=alt.Theta(field="Count", type="quantitative"),
    color=alt.Color(field="Contribution Type", type="nominal"),
    tooltip=[
        alt.Tooltip('Contribution Type', title='Type'),
        alt.Tooltip('Count', title='Count'),
        alt.Tooltip('Percentage', title='Percentage', format='.0%')
        ]
).properties(
    title='Camp Financial Structure'
).interactive()
st.altair_chart(fee_counts_chart, use_container_width=True)


# Count the occurrences of each contribution type
notaflof = filtered_df['NOTAFLOF for low/no income campers?'].value_counts().reset_index()
notaflof.columns = ['NOTAFLOF', 'Count']
notaflof['Percentage'] = (notaflof['Count'] / notaflof['Count'].sum())
notaflof = notaflof.sort_values(by='Count', ascending=True)

notaflof_chart = alt.Chart(notaflof).mark_arc().encode(
    theta=alt.Theta(field="Count", type="quantitative"),
    color=alt.Color(field="NOTAFLOF", type="nominal"),
    tooltip=[
        alt.Tooltip('NOTAFLOF', title='Type'),
        alt.Tooltip('Count', title='Count'),
        alt.Tooltip('Percentage', title='Percentage', format='.0%')
    ]
).properties(
    title='NOTAFLOF for low/no income campers?'
).interactive()
st.altair_chart(notaflof_chart, use_container_width=True)

st.write("Most camps use flat fees, and most offer an informal mechanism to accomodate lower-income campers. Notably, a third of camps don't have a way to support lower-income campers.")

entity = filtered_df['Do you collect contributions through an entity?'].value_counts().reset_index()
entity.columns = ['Entity', 'Count']
entity['Percentage'] = (entity['Count'] / entity['Count'].sum())
entity = entity.sort_values(by='Count', ascending=True)

entity_chart = alt.Chart(entity).mark_arc().encode(
    theta=alt.Theta(field="Count", type="quantitative"),
    color=alt.Color(field="Entity", type="nominal"),
    tooltip=[
        alt.Tooltip('Entity', title='Type'),
        alt.Tooltip('Count', title='Count'),
        alt.Tooltip('Percentage', title='Percentage', format='.0%')
    ]
).properties(
    title='Do you collect contributions through an entity?'
).interactive()
st.altair_chart(entity_chart, use_container_width=True)

st.write("Surprisingly, most camps don't bother with a formal entity!")

st.write("## Drilling into Contributions")
st.write("Next, let's look at the range of contributions for camps that use a tiered contribution system. The blue mark is the average per camper contribution; the red error bars are the upper and lower tiers.")
# QUESTION: How close is the average camper contribution relative to the max/min?
# Error bars of high/mid/low by camp size. 
df2 = filtered_df[filtered_df['Error Lower'].notnull() & filtered_df['Error Upper'].notnull()]

# Using matplotlib

# st.title("Contribution Ranges and Average Contribution vs. Camp Size")
# fig, ax = plt.subplots(figsize=(12, 8))
# ax.errorbar(df2['Camp Size'], df2['Average Per Person Camp Contribution'],
#             yerr=[df2['Error Lower'], df2['Error Upper']],
#             fmt='o', ecolor='red', capsize=5, elinewidth=2, marker='s', markersize=7)

# # Customize the plot
# ax.set_title('Contribution Ranges and Average Contribution vs. Camp Size')
# ax.set_xlabel('Camp Size')
# ax.set_ylabel('Average Contribution Per Person')
# ax.grid(visible=True, which='both', linestyle='--', linewidth=0.5)

# # Display in Streamlit
# st.pyplot(fig)

# using plotly
fig = go.Figure(data=go.Scatter(
    x=df2['Camp Size'],
    y=df2['Average Per Person Camp Contribution'],
    error_y=dict(
        type='data', # or 'percent' for percentage
        symmetric=False,
        array=df2['Error Upper'],
        arrayminus=df2['Error Lower'],
        color='red',
    ),
    mode='markers',
    marker=dict(color='blue', size=10, symbol='square'),
    line=dict(color='red'),
))

# Customize the layout
fig.update_layout(
    title='Contribution Ranges and Average Contribution vs. Camp Size',
    xaxis_title='Camp Size',
    yaxis_title='Average Contribution Per Person',
    template='plotly_white',
    height=500
)

# Add tooltips
fig.update_traces(
    hoverinfo='all',
    hovertemplate="Camp Size: %{x}<br>Average Contribution: %{y:.2f}<br>Error Lower: %{error_y.arrayminus:.2f}<br>Error Upper: %{error_y.array:.2f}<extra></extra>"
)

# Display the plot in Streamlit
st.plotly_chart(fig, use_container_width=True)
# error_bars = alt.Chart(df2).mark_errorbar(extent='ci').encode(
#     x=alt.X('Camp Size:Q', title='Camp Size'),
#     y=alt.Y('Average Per Person Camp Contribution:Q', title='Average Contribution Per Person'),
#     yError='Error Upper:Q',
#     yError2='Error Lower:Q',
#     tooltip=['Camp Size', 'Average Per Person Camp Contribution']
# )

# # Base scatter plot to add markers on the error bars
# base = alt.Chart(df2).mark_point().encode(
#     x='Camp Size:Q',
#     y='Average Per Person Camp Contribution:Q',
#     tooltip=['Camp Size', 'Average Per Person Camp Contribution']
# )

# # Combine the error bars and base markers
# chart = (error_bars + base).interactive()
# st.altair_chart(chart, use_container_width=True)
# QUESTION: How do camp fees vary based on amenities offered?

st.write("Do you provide additional amenities for an additional fee?")
exploded_other_fees = filtered_df['has_extra_paid_in_amenities'].reset_index(drop=True)
# Count the occurrences of each contribution type
exploded_other_fees = exploded_other_fees.value_counts().reset_index()
exploded_other_fees.columns = ['Attl Paid Amenity', 'Count']
exploded_other_fees['Percentage'] = (exploded_other_fees['Count'] / exploded_other_fees['Count'].sum())
exploded_other_fees = exploded_other_fees.sort_values(by='Count', ascending=True)

exploded_other_fees_chart = alt.Chart(exploded_other_fees).mark_arc().encode(
    theta=alt.Theta(field="Count", type="quantitative"),
    color=alt.Color(field="Attl Paid Amenity", type="nominal"),
    tooltip=[
        alt.Tooltip('Attl Paid Amenity', title='Type'),
        alt.Tooltip('Count', title='Count'),
        alt.Tooltip('Percentage', title='Percentage', format='.0%')
        ]
).properties(
    title='Additional Paid-In Amenities'
).interactive()
st.altair_chart(exploded_other_fees_chart, use_container_width=True)
st.write("Some camps structure their fee structure in a way that lets some campers have additional creature comforts, e.g. RV hookup power, without budening other campers. It's incredibly common, apparently!")

st.write("What additional paid-in amenities tend to be offered?")

paidin_amenity_hist_df = filtered_df['Do supplemental contributions support other camp amenities (in addition to core contribution)'].dropna().explode('Do supplemental contributions support other camp amenities (in addition to core contribution)').reset_index(drop=True).rename('Extra Amenities').reset_index()
paidin_amenity_hist = alt.Chart(paidin_amenity_hist_df).mark_bar().encode(
    x=alt.X('Extra Amenities', title="Extra Amenities", sort='-y'),
    y=alt.Y('count()', title='Number of Camps')
).interactive().properties(
    title='Extra $-Supplemented Amenities',
    width=600,
    height=400
)
st.altair_chart(paidin_amenity_hist, use_container_width=True)
amenity_counts = paidin_amenity_hist_df['Extra Amenities'].value_counts().reset_index()
amenity_counts.columns = ['Extra Amenities', 'Number of Camps']
st.table(amenity_counts)

st.write("## Drilling into Amenities")
st.write("How do camp fees vary based on amenities offered?")

df_melted = df[df['Average Per Person Camp Contribution'].notnull()].melt(id_vars=['ndx', 'Average Per Person Camp Contribution'], value_vars=amenity_columns, var_name='Amenity', value_name='Presence')
# grouped_data = df_melted.groupby(['Amenity','Presence'])['Average Per Person Camp Contribution'].describe(percentiles=[.25, .5, .75])
df_melted2 = df_melted[df_melted['Presence'] == 1]

def highlight_diff(s):
    if s.name == 'Percent Difference':
        return ['background-color: lightgreen' if v > 20 else 'background-color: salmon' if v < -20 else '' for v in s]
    return ['' for _ in s]

amenity_pivot = df_melted.pivot_table(
    index='Amenity',
    columns='Presence',
    values='Average Per Person Camp Contribution',
    aggfunc='median'  # Specify the aggregation function, mean in this case
).round()
amenity_pivot['Percent Difference'] = ((amenity_pivot[True] - amenity_pivot[False]) / amenity_pivot[False] * 100).astype(int)
styled_table = amenity_pivot.style.apply(highlight_diff, axis=0).format("{:.0f}", na_rep="N/A", subset=pd.IndexSlice[:, [True, False, 'Percent Difference']])
st.dataframe(styled_table)

# st.write("_Filtering will not work for this chart_")
# boxplot = alt.Chart(df_melted2).mark_boxplot(size=30).encode(
#     x=alt.X('Amenity:N', title='Amenity', sort=list(df_binarized_amenity.columns)),
#     y=alt.Y('Average Per Person Camp Contribution:Q', title='Average Contribution Per Person'),
#     tooltip=['ndx', 'Average Per Person Camp Contribution']
# ).properties(
#     title='Average Contribution vs. Presence of Amenities',
#     width=800,
#     height=400
# ).configure_axisX(labelAngle=-45)
# st.altair_chart(boxplot, use_container_width=True)
# st.write("This boxplot doesn't tell us much overall. So let's do the same avg camper dues boxplot but split it according to if an amenity is offered or not.")

st.write("If you're more of a visual learner, these boxplots show the avg camper dues split it according to if an amenity is offered or not.")


#g = sns.FacetGrid(df_melted, col='Amenity', col_wrap=3, height=4)  # Adjust col_wrap for the number of amenities 
#g.map(sns.boxplot, 'Presence', 'Average Per Person Camp Contribution', showmeans=True)
#plt.savefig('/Users/peter/Downloads/contribution_vs_amenities_boxplot.png')
st.write("_Filtering will not work for these charts. Scroll right ->>> to see each amenity._")
boxplot_subplot = alt.Chart(df_melted).mark_boxplot().encode(
    x=alt.X('Presence:O', title='Amenity is Present'),  # Labels for amenity presence/absence
    y=alt.Y('Average Per Person Camp Contribution:Q', title='Average Contribution Per Person'),
    column=alt.Column('Amenity:N', title=None)  # Split by amenity type
).properties(
    width=150,  # Adjust column width
).configure_axisX(labelAngle=-45)
st.altair_chart(boxplot_subplot, use_container_width=True)

# Let's run a regression. 
model_source_df = df[amenity_columns+['Average Per Person Camp Contribution']].dropna()
X = model_source_df[amenity_columns].astype(int)
y = model_source_df['Average Per Person Camp Contribution']

#assert X.dtypes.all() in ['int64', 'float64'], "Check X for non-numeric values."
#assert y.dtype in ['int64', 'float64'], "Check y for non-numeric values."

X = sm.add_constant(X)
model = sm.OLS(y, X).fit()

st.write("#### Regression Analysis: Average Per Person Camp Contribution")
st.write("Can we use a simple regression to understand which amenities drive camp costs?")

# Display regression summary
st.write("##### Model Summary")
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
st.write("##### Feature Importance, Visualized")
st.write("This visualization shows the coefficient values (Dollar impact to camp dues) for each feature (amenity) used in the regression analysis. Read this as 'x' amenity drives 'coefficient' in $ costs above the baseline.")

st.altair_chart(coef_chart, use_container_width=True)


st.write("What did we learn? I guess not to do this again. This model doesn't seem to have much explanatory power. No way in hell does including things like booze, greywater, and shade structure as camp amenities make dues CHEAPER.\nThere may be a relationship we're not directly seeing because it's not in the survey, like a correlation between these amenetities and a benevolent benefactor/sugar mommy/daddy.\n")

st.write("So let's do another model *adding an indicator that the camp may have a substantial benefactor/sugar mommy/sugar daddy*.")
st.write("I implied the presence of a benefactor by looking at the range of upper-end dues for camps that operated on a sliding scale. Camps which had upper dues greater than 1x the average dues There were only 31 camps (35%) so take this with a grain of salt since not much data to work with.")

# Add some rough indicators if there is an especially rich member
sugar_df = df[df['rng_to_avg'].notnull()].copy()
sugar_df['benefactor'] = 0
sugar_df.loc[(sugar_df['Tidbits'].notnull() & sugar_df['Tidbits'].str.contains('benefactor')), 'benefactor'] = 1
sugar_df.loc[sugar_df['rng_to_avg'] > 1, 'benefactor'] = 1


model_source_df2 = sugar_df[amenity_columns+['Average Per Person Camp Contribution', 'benefactor']].dropna()
X = model_source_df2[amenity_columns + ['benefactor']].astype(int)
y = model_source_df2['Average Per Person Camp Contribution']

#assert X.dtypes.all() in ['int64', 'float64'], "Check X for non-numeric values."
#assert y.dtype in ['int64', 'float64'], "Check y for non-numeric values."

X = sm.add_constant(X)
model2 = sm.OLS(y, X).fit()

# Display regression summary
st.write("##### Sugar Daddy Model Summary")
st.text(model2.summary())

st.write("Well fuck me. That's counterintuitive. What did we learn? Apparently, campers who camp with a sugar mommy/daddy pay more! But again, small sample so let's shrug and say YOLO.")
st.write("***Disclaimer***: I haven't done honest-to-god data analysis in years. I've got no pride of authorship, only shame, so If you're that special someone data scientist who wants do a more robust analysis, HMU. pelbaor@gmail.com")

# import seaborn as sns
# plt.figure(figsize=(14, 8))
# sns.boxplot(x='Amenity', y='Average Per Person Camp Contribution', data=df_melted)
# plt.title('Average Contribution vs. Presence of Amenities')
# plt.xlabel('Amenity')
# plt.ylabel('Average Per Person Contribution')
# plt.xticks(rotation=45, ha='right')
# plt.grid(visible=True, axis='y', linestyle='--', linewidth=0.5)
# plt.savefig('/Users/peter/Downloads/contribution_vs_amenities_boxplot.png')


st.write("#### How truthful were we? Stated vs Implied Budget")
st.write("Let's examine how the explicitly reported total budget matches against a bottoms-up estimate that we calculate by multiplying Camp Size and Average per Person Contribution.")

# validation_scatterplot = alt.Chart(filtered_df.loc[filtered_df['validation_difference'].notnull(), ['implied_budget', 'Camp Total Annual Budget']]).mark_circle(size=60).encode(
#     x=alt.X('implied_budget', title='Implied Total Budget'),
#     y=alt.Y('Camp Total Annual Budget', title='Stated Total Budget'),
#     tooltip=['implied_budget', 'Camp Total Annual Budget']
# ).interactive().properties(
#     title='Stated Budget vs. Implied Budget',
#     width=600,
#     height=400
# )
# validation_trendline = validation_scatterplot.transform_regression(
#     'implied_budget', 'Camp Total Annual Budget', method="linear"
# ).mark_line(color='red')
# final_validation_scatter = validation_scatterplot + validation_trendline
# st.altair_chart(final_validation_scatter, use_container_width=True)

validation_bar = alt.Chart(filtered_df.loc[filtered_df['validation_difference'].notnull(), ['validation_difference']]).mark_bar().encode(
    x=alt.X('validation_difference', bin=alt.Bin(maxbins=50), title="% Difference between Implied and Stated Budget"),
    y=alt.Y('count()', title='Number of Camps')
)
st.altair_chart(validation_bar, use_container_width=True)

st.write("Good news. Ya'lls answers are mostly consistent!")

# st.markdown("[![Click me](//static-file-serving.streamlit.app/~/+/app/static/dog.jpg)](https://streamlit.io)")

