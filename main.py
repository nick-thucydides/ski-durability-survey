import pandas as pd
import altair as alt

pd.set_option('display.max_columns', None)

MIN_COMPANIES_PIE = 5
MIN_COUNT = 10

# [ 1 ]  LOAD AND CLEAN THE DATA
# _____________________________________________________________________________________

df = pd.read_csv('C:/Users/16046/PycharmProjects/dur/survey.csv')



# rename columns
df.rename(columns={"Without considering the retail price of the skis, how satisfied were you with the durability of these skis?"
                   : "satno$",
                   "What issues have you had with your skis? check all that apply": "issues",
                   "Select the company that made the skis":"company",
                   "Considering the retail price of the skis, do you think they're worth the price brand new (MSRP)?"
                   : "sat$",
                   "How often do you ride park?":"park",
                   "How much street have you ridden on your skis?":"street",
                   "Do take good care of your skis? i.e. detuning edges before hitting rails,"
                   " buffing out edge cracks, using epoxy/ptex, storing correctly etc": "care",
                   "If the company wasn't on the list, write the name here. otherwise, skip":"other company",
                   "How would you describe your style of riding?":"riding style",
                   "Feel free to leave any additional comments here":"comments"}, inplace=True)
# print(df.columns)

# 
# lowercase, strip
for column in df.select_dtypes(include=['object']).columns:
    df[column] = df[column].str.lower().str.replace(" ", "")

# replace "other" with company name
df['company'] = df.apply(
    lambda row: row['other company']
    if pd.notna(row['company']) and row['company'].strip() == 'other'
    else row['company'],
    axis=1
)


# combine duplicates
df["company"] = df["company"].str.replace(r"v[öo]?lkl.*", "volkl", regex=True)
df["company"] = df["company"].str.replace(r'^dynastar.*', "dynastar", regex=True)
df["company"] = df["company"].str.replace(r'^rossignol.*', "rossignol", regex=True)
df["company"] = df["company"].str.replace(r'^fat.*', "fatypus", regex=True)
df["company"] = df["company"].str.replace("salomonqst99", "salomon", regex=True)
df["company"] = df["company"].str.replace("seasoneqpt", "season", regex=True)
df["company"] = df["company"].str.replace("salomondepart1.0", "salomon", regex=True)
df['company'] = df['company'].replace(r'^j$', 'jskis', regex=True)
df["company"] = df["company"].str.replace("seasonkin.0", "season", regex=True)
df["company"] = df["company"].str.replace("seasonkin", "season", regex=True)
# print(df["company"].unique())

# map satno$ to integer
response_map = {
    'completelydissatisfied': 1,
    'notverysatisfied': 2,
    'notsure/indifferent': 3,
    'somewhatsatisfied': 4,
    'completelysatisfied': 5
}
# add rating no$ (not regarding price)
df['satisfaction_rating'] = df['satno$'].map(response_map)

response_map_price= {
    "notatalldon'tbuytheseskis": 1,
    'notreally': 2,
    'maybe/notsure': 3,
    'mostly': 4,
    'yesforsure': 5
}
# add rating $ (regarding price)
df['satisfaction_rating_$'] = df['sat$'].map(response_map_price)

# print(df['satisfaction_rating'])

company_continent_map = {
    'vishnu': 'Asia',     'k2': 'Asia',       'line': 'Asia',    'surface': 'Asia',
    'icelantic': 'North America', 'on3p': 'North America', 'moment': 'North America',
    'jskis': 'North America', 'jetskis': 'North America', 'fatypus': 'North America',
    'libtech': 'North America',
    'armada': 'Europe',   'dynastar': 'Europe', 'atomic': 'Europe', 'faction': 'Europe',
    'rossignol': 'Europe','elan': 'Europe',    '4frnt': 'Europe', 'nordica': 'Europe',
    'majesty': 'Europe',  'head': 'Europe',    'volkl': 'Europe', 'season': 'Europe',
    'movement': 'Europe', 'blackcrows': 'Europe','simply': 'Europe','1000': 'Europe',
    'salomon': 'Europe',
}



df["street"] = df["street"].replace({'alot': 'a lot', 'hitafewspotsnowandagain': 'occasionally', 'littletonone': 'little to none'})
df["park"] = df["park"].replace({'alot-mostdaysinthepark': 'a lot', ' sometimes': ' sometimes', ' rarely/never': ' rarely/never'})
df["care"] = df["care"].replace({'yeahi\'mprettydilligent': 'a lot', 'surebutnotasmuchasishould': 'in between', 'nahidon\'treallydoanything': 'little to none'})
df["riding style"] = df["riding style"].replace({'aggressive-lotsofhighspeed/highimpacttricks': 'aggressive', 'somewhereinbetween': 'in between', 'prettylaidback': 'laid back'})



# [2] SKI DISTRIBUTION  ( PIE AND BAR CHARTS)
# _____________________________________________________________________________________

# create new df with only useful info
df_by_company = (
    df.groupby('company')
    .agg(avg_no_price=('satisfaction_rating', 'mean'),
         avg_price=('satisfaction_rating_$', 'mean'),
         med_no_price=('satisfaction_rating', 'median'),
         med_price=('satisfaction_rating_$', 'median'),
         count=('company', 'size'))
    .reset_index()
    .sort_values('count', ascending=False)
)

#  [ FIG 1]
# create bar chart to show distribution of all ski companies
comp_dist = alt.Chart(df_by_company).mark_bar().encode(
    y=alt.Y('company:N', title='', sort='-x'),
    x=alt.X('count:Q', title='')
).properties(title="Skis per Company", width=800, height=800).configure_title(fontSize=25).configure_axis(labelFontSize=18, titleFontSize=20)



#  [ FIG 2]
# create bar chart to show distribution of all ski companies

# group smaller companies together
smallerCompanies = df_by_company[df_by_company['count'] < MIN_COMPANIES_PIE]
combinedCompanies = smallerCompanies['count'].sum()
filtered_df = df_by_company[df_by_company['count'] >= MIN_COMPANIES_PIE].copy()

# add new row for combined ski companies
filtered_df = pd.concat(
    [filtered_df, pd.DataFrame([{'company': 'Other', 'count': combinedCompanies}])],
    ignore_index=True
)
filtered_df = filtered_df.sort_values(by='count', ascending=False)

# print(filtered_df)

pie = alt.Chart(filtered_df).mark_arc().encode(
    theta=alt.Theta('count:Q', title='Count'),  
    color=alt.Color('company:N', title='Company', scale=alt.Scale(scheme='tableau20'),
                    sort=alt.EncodingSortField(
        field='count', 
        order='descending',  
        op='sum'  
    )),
    order=alt.Order('count:Q', sort='ascending')  # Explicit order encoding
)
45
pie.properties(title="Skis per company", width=800, height=800).configure_title(fontSize=25).configure_legend(labelFontSize=25, titleFontSize=25, symbolSize=200)

# [3] Create charts for satisfaction, with and without regard to price
# _____________________________________________________________________________________


df_by_company_bigger = df_by_company.drop(df_by_company[df_by_company['count'] < MIN_COUNT].index)
df_by_company_medium = df_by_company.drop(df_by_company[df_by_company['count'] < MIN_COUNT/2].index)

# melt bigger df for mean + median (no price)
df_no_price_melted = df_by_company_bigger.melt(
    id_vars='company',
    value_vars=['avg_no_price', 'med_no_price'],
    var_name='metric',
    value_name='rating'
)

# melt bigger df for mean + median (with price)
df_price_melted = df_by_company_bigger.melt(
    id_vars='company',
    value_vars=['avg_price', 'med_price'],
    var_name='metric',
    value_name='rating'
)

# melt medium df for mean + median (no price)
df_no_price_melted_medium = df_by_company_medium.melt(
    id_vars='company',
    value_vars=['avg_no_price', 'med_no_price'],
    var_name='metric',
    value_name='rating'
)

# melt medium df for mean + median (with price)
df_price_melted_medium = df_by_company_medium.melt(
    id_vars='company',
    value_vars=['avg_price', 'med_price'],
    var_name='metric',
    value_name='rating'
)

# single bar (largest companies)
no_price = alt.Chart(df_by_company_bigger).mark_bar().encode(
    x=alt.X('company:N', title='Ski Company', sort='-y', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('avg_no_price:Q', title='Avg rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10))
).properties(title="Avg satisfaction by company (not regarding price)", width=700, height=700).configure_title(fontSize=30).configure_axis(labelFontSize=25, titleFontSize=25)

price = alt.Chart(df_by_company_bigger).mark_bar().encode(
    x=alt.X('company:N', title='Ski Company', sort='-y', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('avg_price:Q', title='Avg rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10))
).properties(title="Avg satisfaction by company (regarding price)", width=700, height=700).configure_title(fontSize=30).configure_axis(labelFontSize=25, titleFontSize=25)

# single bar (medium size companies)
no_price_all = alt.Chart(df_by_company_medium).mark_bar().encode(
    x=alt.X('company:N', title='Ski Company', sort='-y', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('avg_no_price:Q', title='Avg rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10))
).properties(title="Avg satisfaction by company (not regarding price)", width=1400, height=700).configure_title(fontSize=30).configure_axis(labelFontSize=25, titleFontSize=25)

price_all = alt.Chart(df_by_company_medium).mark_bar().encode(
    x=alt.X('company:N', title='Ski Company', sort='-y', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('avg_price:Q', title='Avg rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10))
).properties(title="Avg satisfaction by company (regarding price)", width=1400, height=700).configure_title(fontSize=30).configure_axis(labelFontSize=25, titleFontSize=25)

# double bar (bigger)
no_price_w_median = alt.Chart(df_no_price_melted).mark_bar().encode(
    x=alt.X('company:N', title='Ski Company', sort=alt.EncodingSortField(field='rating', op='mean', order='descending'), axis=alt.Axis(labelAngle=0)),
    y=alt.Y('rating:Q', title='Rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10)),
    xOffset='metric:N',
    color=alt.Color('metric:N', title='Metric',
                    legend=alt.Legend(labelExpr="datum.label == 'avg_no_price' ? 'Mean' : 'Median'"))
).properties(title='Mean vs Median Satisfaction by Company (not regarding price)', width=700, height=700).configure_title(fontSize=30).configure_axis(labelFontSize=25, titleFontSize=25).configure_legend(labelFontSize=25, titleFontSize=25, symbolSize=200)

price_w_median = alt.Chart(df_price_melted).mark_bar().encode(
    x=alt.X('company:N', title='Ski Company', sort=alt.EncodingSortField(field='rating', op='mean', order='descending'), axis=alt.Axis(labelAngle=0)),
    y=alt.Y('rating:Q', title='Rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10)),
    xOffset='metric:N',
    color=alt.Color('metric:N', title='Metric',
                    legend=alt.Legend(labelExpr="datum.label == 'avg_price' ? 'Mean' : 'Median'"))
).properties(title='Mean vs Median Satisfaction by Company (regarding price)', width=700, height=700).configure_title(fontSize=30).configure_axis(labelFontSize=25, titleFontSize=25).configure_legend(labelFontSize=25, titleFontSize=25, symbolSize=200)

# double bar (medium)
no_price_all_w_median = alt.Chart(df_no_price_melted_medium).mark_bar().encode(
    x=alt.X('company:N', title='Ski Company', sort=alt.EncodingSortField(field='rating', op='mean', order='descending'), axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('rating:Q', title='Rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10)),
    xOffset='metric:N',
    color=alt.Color('metric:N', title='Metric',
                    legend=alt.Legend(labelExpr="datum.label == 'avg_no_price' ? 'Mean' : 'Median'"))
).properties(title='Mean vs Median Satisfaction by Company (not regarding price)', width=1400, height=700).configure_title(fontSize=30).configure_axis(labelFontSize=25, titleFontSize=25).configure_legend(labelFontSize=25, titleFontSize=25, symbolSize=200)

price_all_w_median = alt.Chart(df_price_melted_medium).mark_bar().encode(
    x=alt.X('company:N', title='Ski Company', sort=alt.EncodingSortField(field='rating', op='mean', order='descending'), axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('rating:Q', title='Rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10)),
    xOffset='metric:N',
    color=alt.Color('metric:N', title='Metric',
                    legend=alt.Legend(labelExpr="datum.label == 'avg_price' ? 'Mean' : 'Median'"))
).properties(title='Mean vs Median Satisfaction by Company (regarding price)', width=1400, height=700).configure_title(fontSize=30).configure_axis(labelFontSize=25, titleFontSize=25).configure_legend(labelFontSize=25, titleFontSize=25, symbolSize=200)



# [4] Create charts for satisfaction, by continent of manufacture
# _____________________________________________________________________________________

cont_df = df[df['company'] != 'heritagelab'].copy()

cont_df['continents'] = cont_df['company'].map(company_continent_map)
# print(cont_df.head(10))
# print(cont_df.groupby('continents')['satisfaction_rating'].mean())


# aggregate by continent
df_by_continent = (
    cont_df.groupby('continents')
    .agg(
        avg_no_price=('satisfaction_rating',   'mean'),
        avg_price   =('satisfaction_rating_$', 'mean'),
        count       =('company',               'size')
    )
    .reset_index()
    .sort_values('count', ascending=False)
)

# skis per continent bar chart
cont_dist = alt.Chart(df_by_continent).mark_bar().encode(
    y=alt.Y('continents:N', title='', sort='-x'),
    x=alt.X('count:Q',      title='Number of skis')
).properties(
    title='Skis per Continent', width=800, height=300
).configure_title(fontSize=25).configure_axis(labelFontSize=18, titleFontSize=20)



# avg satisfaction (no price) by continent
cont_no_price = alt.Chart(df_by_continent).mark_bar().encode(
    x=alt.X('continents:N', title='Continent',
            sort='-y', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('avg_no_price:Q', title='Avg Rating',
            scale=alt.Scale(domain=[0, 5]),
            axis=alt.Axis(tickCount=10))
).properties(
    title='Avg Satisfaction by Continent (not regarding price)',
    width=500, height=500
).configure_title(fontSize=25).configure_axis(labelFontSize=20, titleFontSize=20)



# avg satisfaction (with price) by continent
cont_price = alt.Chart(df_by_continent).mark_bar().encode(
    x=alt.X('continents:N', title='Continent',
            sort='-y', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('avg_price:Q', title='Avg Rating',
            scale=alt.Scale(domain=[0, 5]),
            axis=alt.Axis(tickCount=10))
).properties(
    title='Avg Satisfaction by Continent (regarding price)',
    width=500, height=500
).configure_title(fontSize=25).configure_axis(labelFontSize=20, titleFontSize=20)

# [5] See how satisfaction varies wrt habits (how much street/park they ride, how they take care of their skis, style of riding)
# _____________________________________________________________________________________


street_order = ['little to none', 'occasionally', 'a lot']
care_order = ['little to none', 'in between', 'a lot']  
park_order = ['rarely/never', 'sometimes', 'a lot']
riding_style_order = ['laid back', 'in between', 'aggressive']

# STREET __________________________________
df_street = (
    df.groupby('street').agg(
        avg_no_price=('satisfaction_rating',   'mean'),
        avg_price   =('satisfaction_rating_$', 'mean'),
        count       =('company',               'size')
    ).reset_index()
)

df_street_melted = df_street.melt(
    id_vars='street',
    value_vars=['avg_no_price', 'avg_price'],
    var_name='metric',
    value_name='avg_rating'
)

street_chart = alt.Chart(df_street_melted).mark_bar().encode(
    x=alt.X('street:N', title='Street', sort=street_order, axis=alt.Axis(labelAngle=0)),
    y=alt.Y('avg_rating:Q', title='Avg Rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10)),
    xOffset='metric:N',
    color=alt.Color('metric:N', title='Rating',
                    scale =alt.Scale(range=['steelblue', 'green']),
                    legend=alt.Legend(labelExpr=
                        "datum.label == 'avg_no_price' ? 'Satisfaction' : 'Worth the price'"))
).properties(
    title='Avg Satisfaction by Amount of Street riding',
    width=500, height=400
).configure_title(fontSize=25).configure_axis(labelFontSize=18, titleFontSize=20).configure_legend(labelFontSize=18, titleFontSize=25, symbolSize=200)

# PARK __________________________________

df_park = (
    df.groupby('park').agg(
        avg_no_price=('satisfaction_rating',   'mean'),
        avg_price   =('satisfaction_rating_$', 'mean'),
        count       =('company',               'size')
    ).reset_index()
)

df_park_melted = df_park.melt(
    id_vars='park',
    value_vars=['avg_no_price', 'avg_price'],
    var_name='metric',
    value_name='avg_rating'
)

park_chart = alt.Chart(df_park_melted).mark_bar().encode(
    x=alt.X('park:N', title='Park', sort=park_order, axis=alt.Axis(labelAngle=0)),
    y=alt.Y('avg_rating:Q', title='Avg Rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10)),
    xOffset='metric:N',
    color=alt.Color('metric:N', title='Rating',
                    scale =alt.Scale(range=['steelblue', 'green']),
                    legend=alt.Legend(labelExpr=
                        "datum.label == 'avg_no_price' ? 'Satisfaction' : 'Worth the price'"))
).properties(
    title='Avg Satisfaction by Amount of Park skiing',
    width=500, height=400
).configure_title(fontSize=25).configure_axis(labelFontSize=18, titleFontSize=20).configure_legend(labelFontSize=18, titleFontSize=25, symbolSize=200)

# CARE __________________________________
df_care = (
    df.groupby('care').agg(
        avg_no_price=('satisfaction_rating', 'mean'),
        avg_price=('satisfaction_rating_$', 'mean'),
        count=('company', 'size')
    ).reset_index()
)

df_care_melted = df_care.melt(
    id_vars='care',
    value_vars=['avg_no_price', 'avg_price'],
    var_name='metric',
    value_name='avg_rating'
)

care_chart = alt.Chart(df_care_melted).mark_bar().encode(
    x=alt.X('care:N', title='Care Level', sort=care_order, axis=alt.Axis(labelAngle=0)),
    y=alt.Y('avg_rating:Q', title='Avg Rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10)),
    xOffset='metric:N',
    color=alt.Color('metric:N', title='Rating',
                    scale =alt.Scale(range=['steelblue', 'green']),
                    legend=alt.Legend(labelExpr=
                        "datum.label == 'avg_no_price' ? 'Satisfaction' : 'Worth the price'"))
).properties(
    title='Avg Satisfaction by Care Level',
    width=500, height=400
).configure_title(fontSize=25).configure_axis(labelFontSize=18, titleFontSize=20).configure_legend(labelFontSize=18, titleFontSize=25, symbolSize=200)


# RIDING STYLE __________________________________
df_style = (
    df.groupby('riding style').agg(
        avg_no_price=('satisfaction_rating', 'mean'),
        avg_price=('satisfaction_rating_$', 'mean'),
        count=('company', 'size')
    ).reset_index()
)

df_style_melted = df_style.melt(
    id_vars='riding style',
    value_vars=['avg_no_price', 'avg_price'],
    var_name='metric',
    value_name='avg_rating'
)

style_chart = alt.Chart(df_style_melted).mark_bar().encode(
    x=alt.X('riding style:N', title='Riding Style', sort=riding_style_order, axis=alt.Axis(labelAngle=0)),
    y=alt.Y('avg_rating:Q', title='Avg Rating', scale=alt.Scale(domain=[0, 5]), axis=alt.Axis(tickCount=10)),
    xOffset='metric:N',
    color=alt.Color('metric:N', title='Rating',
                    scale =alt.Scale(range=['steelblue', 'green']),
                    legend=alt.Legend(labelExpr=
                        "datum.label == 'avg_no_price' ? 'Satisfaction' : 'Worth the price'"))
).properties(
    title='Avg Satisfaction by Riding Style',
    width=500, height=400
).configure_title(fontSize=25).configure_axis(labelFontSize=18, titleFontSize=20).configure_legend(labelFontSize=18, titleFontSize=25, symbolSize=200)

# _____________________________________________________

df_issues = (
    df['issues']
    .dropna()
    .str.split(',')
    .explode()
    .str.strip()
    .value_counts()
    .reset_index()
)
df_issues.columns = ['issue', 'count']


issues_chart = alt.Chart(df_issues.head(3)).mark_bar().encode(
    x=alt.X('issue:N', title='', sort='-x' ,axis=alt.Axis(labelAngle=0)),
    y=alt.Y('count:Q', title='Count')
).properties(
    title='Issues Reported',
    width=800, height=400
).configure_title(fontSize=25).configure_axis(labelFontSize=18, titleFontSize=20)


issues_chart.save("issues.html")

def violin_box(source_df, rating_col, title):
    counts = source_df['company'].value_counts()
    top_companies = counts[counts >= MIN_COUNT].index.tolist()
    df_filtered = source_df[source_df['company'].isin(top_companies)][['company', rating_col]].dropna()

    violin = (
        alt.Chart(df_filtered)
        .transform_density(
            rating_col,
            as_=[rating_col, 'density'],
            groupby=['company'],
            extent=[1, 5],
            steps=200,
        )
        .mark_area(orient='horizontal', opacity=0.4)
        .encode(
            y=alt.Y(f'{rating_col}:Q',
                    title='Rating',
                    scale=alt.Scale(domain=[1, 5]),
                    axis=alt.Axis(tickCount=5)),
            x=alt.X('density:Q',
                    title='',
                    stack='center',
                    impute=None,
                    axis=alt.Axis(labels=False, values=[0], grid=False, ticks=True)),
            color=alt.Color('company:N', scale=alt.Scale(scheme='tableau10'), legend=None),
        )
    )


    return (
        violin
        .properties(width=110, height=300)
        .facet(
            column=alt.Column(
                'company:N',
                title=title,
                header=alt.Header(titleFontSize=22, labelFontSize=16),
                sort=alt.SortField(field='company', order='ascending'),
            )
        )
        .resolve_scale(x='independent')
    )

violin_no_price = violin_box(df, 'satisfaction_rating',   'Satisfaction by Company (not regarding price)')
violin_price    = violin_box(df, 'satisfaction_rating_$', 'Satisfaction by Company (regarding price)')

def box_plot(source_df, rating_col, title):
    counts = source_df['company'].value_counts()
    top_companies = counts[counts >= MIN_COUNT].index.tolist()
    df_filtered = source_df[source_df['company'].isin(top_companies)][['company', rating_col]].dropna()

    box = (
        alt.Chart(df_filtered)
        .mark_boxplot(
            median=alt.MarkConfig(color='red', size=30),
            box=alt.MarkConfig(opacity=0.9),
            outliers=alt.MarkConfig(size=20, opacity=0.6),
            size=30,
            ticks=True,
        )
        .encode(
            y=alt.Y(f'{rating_col}:Q',
                    title='Rating',
                    scale=alt.Scale(domain=[1, 5]),
                    axis=alt.Axis(tickCount=5)),
            x=alt.value(0),
            color=alt.Color('company:N', scale=alt.Scale(scheme='tableau10'), legend=None),
        )
    )

    return (
        alt.layer(box)
        .properties(width=80, height=300)
        .facet(
            column=alt.Column(
                'company:N',
                title=title,
                header=alt.Header(titleFontSize=22, labelFontSize=16),
                sort=alt.SortField(field='company', order='ascending'),
            )
        )
        .resolve_scale(x='independent')
    )

def rating_histograms(source_df, rating_col, title):
    counts = source_df['company'].value_counts()
    top_companies = counts[counts >= MIN_COUNT].index.tolist()

    df_filtered = source_df[
        source_df['company'].isin(top_companies)
    ][['company', rating_col]].dropna()

    chart = (
        alt.Chart(df_filtered)
        .mark_bar()
        .encode(
            x=alt.X(
                f'{rating_col}:O',
                title='Rating',
                sort=[1, 2, 3, 4, 5],
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                'count():Q',
                title='Count'
            ),
            color=alt.Color(
                'company:N',
                scale=alt.Scale(scheme='tableau10'),
                legend=None
            )
        )
        .properties(
            width=110,
            height=300
        )
        .facet(
            column=alt.Column(
                'company:N',
                title=title,
                header=alt.Header(
                    titleFontSize=22,
                    labelFontSize=16
                ),
                sort=alt.SortField(
                    field='company',
                    order='ascending'
                )
            )
        )
    )

    return chart

hist_no_price = rating_histograms(
    df,
    'satisfaction_rating',
    'Satisfaction by Company (not regarding price)'
)

hist_price = rating_histograms(
    df,
    'satisfaction_rating_$',
    'Satisfaction by Company (regarding price)'
)

box_no_price = box_plot(df, 'satisfaction_rating',   'Satisfaction by Company (not regarding price)')
box_price = box_plot(df, 'satisfaction_rating_$', 'Satisfaction by Company (regarding price)')

box_no_price.save("box_no_price.html")
box_price.save("box_price.html")
comp_dist.save("skis per company chart.html")
pie.save("pie.html")
cont_dist.save("skis_per_continent.html")
hist_no_price.save("hist_no_price.html")
hist_price.save("hist_price.html")
cont_no_price.save("continent_satisfaction_no_price.html")
cont_price.save("continent_satisfaction_price.html")
price.save("price.html")
no_price.save("no_price.html")
price_w_median.save("price_w_median.html")        
no_price_w_median.save("no_price_w_median.html")
price_all.save("price_all.html")
no_price_all.save("no_price_all.html")
price_all_w_median.save("price_all_w_median.html") 
no_price_all_w_median.save("no_price_all_w_median.html")


street_chart.save("street_satisfaction.html")
park_chart.save("park_satisfaction.html")
care_chart.save("care_satisfaction.html")
style_chart.save("style_satisfaction.html")

violin_no_price.save("violin_no_price.html")
violin_price.save("violin_price.html")


