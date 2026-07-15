from extract import extract_data
from transform import transform_data
from load import build_star_schema

df1, df2 = extract_data()

df_analysis = transform_data(df1, df2)

build_star_schema(df_analysis)

print("Pipeline completed successfully")