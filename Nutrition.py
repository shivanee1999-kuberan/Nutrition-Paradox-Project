
import requests
import pandas as pd
import pycountry
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector



api_urls = {
    "adult_obesity": "https://ghoapi.azureedge.net/api/NCD_BMI_30C",
    "child_obesity": "https://ghoapi.azureedge.net/api/NCD_BMI_PLUS2C",
    "adult_malnutrition": "https://ghoapi.azureedge.net/api/NCD_BMI_18C",
    "child_malnutrition": "https://ghoapi.azureedge.net/api/NCD_BMI_MINUS2C"
}

#fetching data from url and converting to json

json_data = {}

for key, url in api_urls.items():
    response = requests.get(url)
    response.raise_for_status()
    json_data[key] = response.json()

# json to dataframe

df_adult_obesity = pd.DataFrame(json_data["adult_obesity"]["value"])
df_child_obesity = pd.DataFrame(json_data["child_obesity"]["value"])

df_adult_malnutrition = pd.DataFrame(json_data["adult_malnutrition"]["value"])
df_child_malnutrition = pd.DataFrame(json_data["child_malnutrition"]["value"])

# adding age_group column

df_adult_obesity["age_group"] = "Adult"
df_child_obesity["age_group"] = "Child/Adolescent"

df_adult_malnutrition["age_group"] = "Adult"
df_child_malnutrition["age_group"] = "Child/Adolescent"

# combining adult and child data

df_obesity = pd.concat(
    [df_adult_obesity, df_child_obesity],
    ignore_index=True
)

df_malnutrition = pd.concat(
    [df_adult_malnutrition, df_child_malnutrition],
    ignore_index=True
)

# Filter year 2012 - 2022
df_obesity = df_obesity[
    (df_obesity["TimeDim"] >= 2012) & (df_obesity["TimeDim"] <= 2022)
]

df_malnutrition = df_malnutrition[
    (df_malnutrition["TimeDim"] >= 2012) & (df_malnutrition["TimeDim"] <= 2022)
]

df_obesity["Dim1"] = df_obesity["Dim1"].replace({
    "SEX_MLE" : "MALE",
    "SEX_FMLE" : "FEMALE",
    "SEX_BTSX" : "BOTH"
})

df_malnutrition["Dim1"] = df_malnutrition["Dim1"].replace({
    "SEX_MLE": "MALE",
    "SEX_FMLE": "FEMALE",
    "SEX_BTSX": "BOTH"
})    

# keeping columns and rename

columns_to_keep = [
    "ParentLocation",
    "Dim1",
    "TimeDim",
    "Low",
    "High",
    "NumericValue",
    "SpatialDim",
    "age_group"
]

rename_map = {
    "ParentLocation": "Region",
    "Dim1": "Gender",
    "TimeDim": "Year",
    "Low": "LowerBound",
    "High": "UpperBound",
    "NumericValue": "Mean_Estimate",
    "SpatialDim": "Country"
}



df_obesity_clean = df_obesity[columns_to_keep].rename(columns=rename_map)
df_malnutrition_clean = df_malnutrition[columns_to_keep].rename(columns=rename_map)


# Country code conversion
special_cases = {
    'GLOBAL': 'Global',
    'AFR': 'Africa',
    'SEAR': 'South-East Asia Region',
    'EUR': 'Europe',
    'EMR': 'Eastern Mediterranean Region',
    'WPR': 'Western Pacific Region',
    'AMR': 'Americas Region',
    'WB_LMI': 'Low & Middle Income',
    'WB_HI': 'High Income',
    'WB_LI': 'Low Income',
    'WB_UMI': 'Upper Middle Income'
}

def convert_country(code):
    if pd.isna(code):
        return code
    if code in special_cases:
        return special_cases[code]
    country = pycountry.countries.get(alpha_3=code)
    return country.name if country else code

df_obesity_clean["Country"] = df_obesity_clean["Country"].apply(convert_country)
df_malnutrition_clean["Country"] = df_malnutrition_clean["Country"].apply(convert_country)

# 10. adding CI_WIDTH column

df_obesity_clean["CI_Width"] = (
    df_obesity_clean["UpperBound"] - df_obesity_clean["LowerBound"]
)

df_malnutrition_clean["CI_Width"] = (
    df_malnutrition_clean["UpperBound"] - df_malnutrition_clean["LowerBound"]
)

# 11. adding obesity_level column

def obesity_level(mean):
    if mean >= 30:
        return "High"
    elif mean >= 25:
        return "Moderate"
    else:
        return "Low"

df_obesity_clean["obesity_level"] = (
    df_obesity_clean["Mean_Estimate"].apply(obesity_level)
)

# 12. adding malnutrition_level column

def malnutrition_level(mean):
    if mean >= 20:
        return "High"
    elif mean >= 10:
        return "Moderate"
    else:
        return "Low"

df_malnutrition_clean["malnutrition_level"] = (
    df_malnutrition_clean["Mean_Estimate"].apply(malnutrition_level)
)

# 13. Verification CHECK

print(df_obesity_clean.columns)
print(df_malnutrition_clean.columns)

# 14. Convert to csv file

df_obesity_clean.to_csv("final_obesity_data.csv", index=False)
df_malnutrition_clean.to_csv("final_malnutrition_data.csv", index=False)

# Exploratory Data Analysis

df_obesity = pd.read_csv("final_obesity_data.csv")
df_malnutrition = pd.read_csv("final_malnutrition_data.csv")

# print(df_obesity.shape)
# print(df_malnutrition.shape)

# print(df_obesity.info())

# missing and unusual values

print(df_obesity.isna().sum())
print(df_malnutrition.isna().sum())

# Mean estimate for obesity and malnutrition
plt.figure(figsize=(8,5))
sns.histplot(df_obesity["Mean_Estimate"], kde=True)
plt.title("Distribution of Mean Estimate - Obesity")
plt.xlabel("Mean_Estimate")
plt.ylabel("Count")
plt.show()

plt.figure(figsize=(8,5))
sns.histplot(df_malnutrition["Mean_Estimate"], kde=True)
plt.title("Distribution of Mean Estimate - Malnutrition")
plt.xlabel("Mean_Estimate")
plt.ylabel("Count")
plt.show()

# plt.tight_layout()
# plt.show()

# CI_width for obesity and malnutrition

plt.figure(figsize=(8,6))
sns.histplot(df_obesity['CI_Width'], kde=True)
plt.title("Distribution of Confidence Interval Width")
plt.xlabel("CI_Width")
plt.ylabel("Count")
plt.show()

plt.figure(figsize=(8,6))
sns.histplot(df_malnutrition['CI_Width'], kde=True)
plt.title("Distribution of Confidence Interval Width")
plt.xlabel("CI_Width")
plt.ylabel("Count")
plt.show()

# Analyzing trend

obesity_trend = df_obesity.groupby("Year")["Mean_Estimate"].mean()

plt.figure(figsize=(8,5))
plt.plot(obesity_trend.index, obesity_trend.values, marker='o')
plt.title("Global Obesity Trend (2012 - 2022)")
plt.xlabel("Year")
plt.ylabel("Average Obesity (%)")
plt.show()

malnutrition_trend = df_malnutrition.groupby("Year")["Mean_Estimate"].mean()

plt.figure (figsize=(8,5))
plt.plot(malnutrition_trend.index, malnutrition_trend.values, marker='o')
plt.title("Global Malnutrition Trend (2012 - 2022)")
plt.xlabel("Year")
plt.ylabel("Average Malnutrition (%)")
plt.show()

# Analysing regionwise

plt.figure(figsize=(8,5))
sns.barplot(data=df_obesity,
            x="Region",
            y="Mean_Estimate",
            estimator="mean"
            )
plt.xticks(rotation=45)
plt.title("Average obesity by Region")
plt.show()

plt.figure(figsize=(8,5))
sns.barplot(data=df_malnutrition,
            x="Region",
            y="Mean_Estimate",
            estimator="mean"
            )
plt.xticks(rotation=45)
plt.title("Average Malnutrition by Region")
plt.show()

# Genderwise Analysis

plt.figure(figsize=(8,5))
sns.boxplot(data=df_obesity,
            x="Gender",
            y="Mean_Estimate",
            )

plt.title("Average Obesity by Gender")
plt.show()

plt.figure(figsize=(8,5))
sns.boxplot(data=df_malnutrition,
            x="Gender",
            y="Mean_Estimate",
            )
plt.title("Average Malnutrition by Gender")
plt.show()

# Analysis by age group

plt.figure(figsize=(8,5))
sns.boxplot(data=df_obesity,
            x="age_group",
            y="Mean_Estimate")
plt.title("Obesity Level by Age Group")
plt.show()

plt.figure(figsize=(8,5))
sns.boxplot(data=df_malnutrition,
            x="age_group",
            y="Mean_Estimate")
plt.title("Malnutrition Level by Age Group")
plt.show()

# Obesity vs Malnutrition

plt.figure(figsize=(8,5))
sns.boxplot(data=pd.concat([
    df_obesity.assign(Type="Obesity"),
    df_malnutrition.assign(Type="Malnutrition")
]),
x="Type",
y="Mean_Estimate")
plt.title("Obesity vs Malnutrition Comparision")
plt.show()

# Connection to SQL

import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Shiva@1999",
    database="nutrition_paradox"
)

cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS obesity (
    Region VARCHAR(100),
    Gender VARCHAR(20),
    Year INT,
    LowerBound FLOAT,
    UpperBound FLOAT,
    Mean_Estimate FLOAT,
    Country VARCHAR(100),
    age_group VARCHAR(30),
    CI_Width FLOAT,
    obesity_level VARCHAR(20)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS malnutrition (
    Region VARCHAR(100),
    Gender VARCHAR(20),
    Year INT,
    LowerBound FLOAT,
    UpperBound FLOAT,
    Mean_Estimate FLOAT,
    Country VARCHAR(100),
    age_group VARCHAR(30),
    CI_Width FLOAT,
    malnutrition_level VARCHAR(20)
)
""")

conn.commit()

print("Tables created successfully")

# cursor.close()
# conn.close()

# Obesity table insert datas

print("Obesity rows:", df_obesity_clean.shape)
print("Malnutrition rows:", df_malnutrition_clean.shape)


insert_obesity_query = """
INSERT INTO obesity (
    Region, Gender, Year, LowerBound, UpperBound,
    Mean_Estimate, Country, age_group, CI_Width, obesity_level
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# for _, row in df_obesity_clean.iterrows():
#     cursor.execute(insert_obesity_query, tuple(row))

# Malnutrition table insert datas

insert_malnutrition_query = """
INSERT INTO malnutrition (
    Region, Gender, Year, LowerBound, UpperBound,
    Mean_Estimate, Country, age_group, CI_Width, malnutrition_level
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# for _, row in df_malnutrition_clean.iterrows():
#     cursor.execute(insert_malnutrition_query, tuple(row))
cursor.execute("DELETE FROM obesity")
cursor.execute("DELETE FROM malnutrition")
conn.commit()

cursor.executemany(insert_obesity_query, df_obesity_clean.values.tolist())
cursor.executemany(insert_malnutrition_query, df_malnutrition_clean.values.tolist())


conn.commit()
print("Data inserted successfully into MySQL")


Obesity_queries = {
"Q1_Top_5_Regions_2022": """
SELECT 
    Region,
    ROUND(AVG(Mean_Estimate), 2) AS avg_obesity
FROM obesity
WHERE Year = 2022
GROUP BY Region
ORDER BY avg_obesity DESC
LIMIT 5;
""",

"Q2_Top_5_Countries": """
SELECT
      Country,
      ROUND(AVG(Mean_Estimate), 2) AS avg_obesity
FROM obesity
GROUP BY Country
ORDER BY avg_obesity DESC
LIMIT 5;
""",

"Q3_India_Obesity_MeanEstimate" :"""
SELECT
      Year,
      ROUND(AVG(Mean_Estimate), 2) AS avg_obesity
FROM obesity
WHERE Country = 'India'
GROUP BY Year
ORDER BY Year;
""",

"Q4_Avg_Obesity_by_Gender" : """
SELECT
    Gender,
    ROUND(AVG(Mean_Estimate), 2)AS avg_obesity
FROM obesity
GROUP BY Gender
""",

"Q5_Couuntry_Count_by_Level_Age" : """
SELECT
    obesity_level,
    age_group,
    COUNT(DISTINCT Country) AS country_count
FROM obesity
GROUP BY obesity_level, age_group 
""",

"Q6_Least_Reliable" : """
SELECT
    Country,
    ROUND(AVG(CI_Width), 2) AS avg_ci_width
FROM obesity
GROUP BY Country
ORDER BY avg_ci_width DESC
LIMIT 5;
""",

"Q6b_Most_Consistent" : """
SELECT
    Country,
    ROUND(AVG(CI_Width), 2) AS avg_ci_width
FROM obesity
GROUP BY Country
ORDER BY avg_ci_width ASC
LIMIT 5;
""",

"Q7_Avg_by_Age_Group" : """
SELECT
    age_group,
    ROUND(AVG(Mean_Estimate), 2) AS avg_obesity
FROM obesity
GROUP BY age_group
""",

"Q8_Consistent_Low_Obesity" : """
SELECT
    Country,
    ROUND(AVG(Mean_Estimate),2) AS avg_obesity,
    ROUND(AVG(CI_Width),2) AS avg_ci
FROM obesity
GROUP BY Country
HAVING avg_obesity < 10 AND avg_ci < 5
ORDER BY avg_obesity ASC
LIMIT 10;
""",

"Q9_Female_Greater_Than_Male" : """
SELECT
    o1.Country,
    o1.Year,
    ROUND(o1.Mean_Estimate - o2.Mean_Estimate, 2) AS diff
FROM obesity o1
JOIN obesity o2
ON o1.Country = o2.Country
AND o1.Year = o2.Year
WHERE o1.Gender = 'FEMALE'
AND o2.Gender = 'MALE'
AND o1.Mean_Estimate > o2.Mean_Estimate;
""",

"Q10_Global_Avg_Per_Year" : """
SELECT
    Year,
    ROUND(AVG(Mean_Estimate), 2) AS global_avg_obesity
FROM obesity
GROUP BY Year
ORDER BY Year;
"""

}

Obesity_results = {}

for name, sql in Obesity_queries.items():
    print(f"\n==={name}===")
    df = pd.read_sql_query(sql,conn)
    print(df)
    Obesity_results[name] = df


Malnutrition_queries = {

"Q1_Avg_Malnutrition_By_Age_Group" : """
SELECT
    age_group,
    ROUND(AVG(Mean_Estimate), 2)  AS avg_malnutrition
FROM malnutrition
GROUP BY age_group;
""",

"Q2_Top_5_Countries_Malnutrition" : """
SELECT 
    Country,
    ROUND(AVG(Mean_Estimate), 2) AS avg_malnutrition
FROM malnutrition
GROUP BY Country
ORDER BY avg_malnutrition DESC
LIMIT 5;
""",

"Q3_Africa_Malnutrition_By_Year" : """
SELECT
    Year,
    ROUND(AVG(Mean_Estimate), 2) AS avg_malnutrition
FROM malnutrition
WHERE Region = 'Africa'
GROUP BY Year
ORDER BY Year;
""",

"Q4_Avg_Malnurition_By_Gender" : """
SELECT
    Gender,
    ROUND(AVG(Mean_Estimate), 2) AS avg_malnutrition
FROM malnutrition
GROUP BY Gender;
""",

"Q5_Malnutrition_Levelwise_CIWidth_AgeGroup" : """
SELECT
    malnutrition_level,
    age_group,
    ROUND(AVG(CI_Width), 2)AS avg_ci_width
FROM malnutrition
GROUP BY malnutrition_level, age_group;
""",

"Q6_Malnutrition_in_Selected_Country" : """
SELECT
    Country,
    Year,
    ROUND(AVG(Mean_Estimate), 2) AS avg_malnutrition
FROM malnutrition
WHERE Country IN ('India', 'Nigeria', 'Brazil')
GROUP BY Country, Year
ORDER BY Country, Year;
""",

"Q7_Lowest_Malnutrition_Regions" : """
SELECT
    Region,
    ROUND(AVG(Mean_Estimate), 2) AS avg_malnutrition
FROM malnutrition
GROUP BY Region
ORDER BY avg_malnutrition ASC
LIMIT 5;
""",

"Q8_Increasing_Malnutrition_By_Country" : """
SELECT
    Country,
    MAX(Mean_Estimate) - MIN(Mean_Estimate) AS change_value
FROM malnutrition
GROUP BY Country
HAVING change_value > 0 
ORDER BY change_value DESC;
""",

"Q9_MIN_MAX_Malnutrition_Yearwise" : """
SELECT
    Year,
    MIN(Mean_Estimate) AS min_malnutrition,
    MAX(Mean_Estimate) AS max_malnutrition
FROM malnutrition
GROUP BY Year
ORDER BY Year;
""",

"Q10_High_CIWidth_Flags" : """
SELECT
    Country,
    Year,
    CI_Width
FROM malnutrition
WHERE CI_Width > 5
ORDER BY CI_Width desc;
"""

}

Malnutrition_results = {}

for name,sql in Malnutrition_queries.items():
    print(f"\n==={name}===")
    df = pd.read_sql_query(sql,conn)
    print(df)
    Malnutrition_results[name] = df

# Joint Qurey's

Combined_queries = {

    
    "Q1_Obesity_vs_Malnutrition_By_Country": """
    SELECT
        o.Country,
        ROUND(AVG(o.Mean_Estimate), 2) AS avg_obesity,
        ROUND(AVG(m.Mean_Estimate), 2) AS avg_malnutrition
    FROM obesity o
    JOIN malnutrition m
        ON o.Country = m.Country
       AND o.Year = m.Year
    WHERE o.Country IN ('India', 'USA', 'Nigeria', 'Brazil', 'Japan')
    GROUP BY o.Country;
    """,

    
    "Q2_Gender_Disparity": """
    SELECT
        o.Gender,
        ROUND(AVG(o.Mean_Estimate), 2) AS avg_obesity,
        ROUND(AVG(m.Mean_Estimate), 2) AS avg_malnutrition
    FROM obesity o
    JOIN malnutrition m
        ON o.Country = m.Country
       AND o.Year = m.Year
       AND o.Gender = m.Gender
    GROUP BY o.Gender;
    """,

    
    "Q3_Regionwise_Africa_vs_Americas": """
    SELECT
        o.Region,
        ROUND(AVG(o.Mean_Estimate), 2) AS avg_obesity,
        ROUND(AVG(m.Mean_Estimate), 2) AS avg_malnutrition
    FROM obesity o
    JOIN malnutrition m
        ON o.Country = m.Country
       AND o.Year = m.Year
    WHERE o.Region IN ('Africa', 'Americas Region')
    GROUP BY o.Region;
    """,

    
    "Q4_Obesity_Up_Malnutrition_Down": """
    SELECT
        o.Country,
        MAX(o.Mean_Estimate) - MIN(o.Mean_Estimate) AS obesity_change,
        MAX(m.Mean_Estimate) - MIN(m.Mean_Estimate) AS malnutrition_change
    FROM obesity o
    JOIN malnutrition m
        ON o.Country = m.Country
       AND o.Year = m.Year
    GROUP BY o.Country
    HAVING obesity_change > 0
       AND malnutrition_change < 0;
    """,

    
    "Q5_Agewise_Trend": """
    SELECT
        o.age_group,
        ROUND(AVG(o.Mean_Estimate), 2) AS avg_obesity,
        ROUND(AVG(m.Mean_Estimate), 2) AS avg_malnutrition
    FROM obesity o
    JOIN malnutrition m
        ON o.Country = m.Country
       AND o.Year = m.Year
       AND o.age_group = m.age_group
    GROUP BY o.age_group;
    """
}


Combined_results = {}

for name, sql in Combined_queries.items():
    print(f"\n=== {name} ===")
    df = pd.read_sql_query(sql, conn)

    # IMPORTANT: do NOT print full dataframe
    print("Shape:", df.shape)
    print(df.head())

    Combined_results[name] = df

cursor.close()
conn.close()
print("MySQL connection closed")


























































