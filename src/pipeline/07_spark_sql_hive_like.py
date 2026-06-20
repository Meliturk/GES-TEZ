from pathlib import Path
from pyspark.sql import SparkSession

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "solar_data"
OUTPUT_DIR = PROJECT_DIR / "spark_outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

spark = SparkSession.builder \
    .appName("GES Spark SQL Hive Like Analysis") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

def read_csv(path):
    return spark.read.option("header", True).option("inferSchema", True).csv(str(path))

def save_query_result(df, file_name):
    output_file = OUTPUT_DIR / file_name
    df.toPandas().to_csv(output_file, index=False, encoding="utf-8-sig")
    print("Kaydedildi:", output_file)

print("Spark SQL / Hive benzeri analiz basladi...")

plant1 = read_csv(DATA_DIR / "Plant_1_Anomaly_Data.csv")
plant2 = read_csv(DATA_DIR / "Plant_2_Anomaly_Data.csv")

plant1.createOrReplaceTempView("plant1_anomaly_table")
plant2.createOrReplaceTempView("plant2_anomaly_table")

print("\nGecici SQL tablolari olusturuldu:")
print("- plant1_anomaly_table")
print("- plant2_anomaly_table")

q1 = spark.sql("""
SELECT
    'Plant 1' AS PLANT,
    COUNT(*) AS TOTAL_ROWS,
    SUM(CASE WHEN ANOMALY = true THEN 1 ELSE 0 END) AS ANOMALY_COUNT,
    ROUND((SUM(CASE WHEN ANOMALY = true THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS ANOMALY_RATE_PERCENT
FROM plant1_anomaly_table

UNION ALL

SELECT
    'Plant 2' AS PLANT,
    COUNT(*) AS TOTAL_ROWS,
    SUM(CASE WHEN ANOMALY = true THEN 1 ELSE 0 END) AS ANOMALY_COUNT,
    ROUND((SUM(CASE WHEN ANOMALY = true THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS ANOMALY_RATE_PERCENT
FROM plant2_anomaly_table
""")

print("\nSQL Sorgu 1 - Santral bazli anomali ozeti:")
q1.show(truncate=False)

q2 = spark.sql("""
SELECT
    SOURCE_KEY,
    COUNT(*) AS ANOMALY_COUNT,
    ROUND(AVG(POWER_GAP), 2) AS AVG_POWER_GAP,
    ROUND(MAX(POWER_GAP), 2) AS MAX_POWER_GAP
FROM plant1_anomaly_table
WHERE ANOMALY = true
GROUP BY SOURCE_KEY
ORDER BY ANOMALY_COUNT DESC
LIMIT 10
""")

print("\nSQL Sorgu 2 - Plant 1 en cok anomali veren SOURCE_KEY:")
q2.show(truncate=False)

q3 = spark.sql("""
SELECT
    SOURCE_KEY,
    COUNT(*) AS ANOMALY_COUNT,
    ROUND(AVG(POWER_GAP), 2) AS AVG_POWER_GAP,
    ROUND(MAX(POWER_GAP), 2) AS MAX_POWER_GAP
FROM plant2_anomaly_table
WHERE ANOMALY = true
GROUP BY SOURCE_KEY
ORDER BY ANOMALY_COUNT DESC
LIMIT 10
""")

print("\nSQL Sorgu 3 - Plant 2 en cok anomali veren SOURCE_KEY:")
q3.show(truncate=False)

q4 = spark.sql("""
SELECT
    TO_DATE(DATE_TIME) AS DATE,
    COUNT(*) AS ANOMALY_COUNT
FROM plant1_anomaly_table
WHERE ANOMALY = true
GROUP BY TO_DATE(DATE_TIME)
ORDER BY ANOMALY_COUNT DESC
LIMIT 10
""")

print("\nSQL Sorgu 4 - Plant 1 gun bazli anomali:")
q4.show(truncate=False)

q5 = spark.sql("""
SELECT
    TO_DATE(DATE_TIME) AS DATE,
    COUNT(*) AS ANOMALY_COUNT
FROM plant2_anomaly_table
WHERE ANOMALY = true
GROUP BY TO_DATE(DATE_TIME)
ORDER BY ANOMALY_COUNT DESC
LIMIT 10
""")

print("\nSQL Sorgu 5 - Plant 2 gun bazli anomali:")
q5.show(truncate=False)

save_query_result(q1, "spark_sql_plant_summary.csv")
save_query_result(q2, "spark_sql_plant1_top_sources.csv")
save_query_result(q3, "spark_sql_plant2_top_sources.csv")
save_query_result(q4, "spark_sql_plant1_top_days.csv")
save_query_result(q5, "spark_sql_plant2_top_days.csv")

summary_path = OUTPUT_DIR / "spark_sql_hive_like_summary.txt"

with open(summary_path, "w", encoding="utf-8") as f:
    f.write("SPARK SQL / HIVE BENZERI ANALIZ OZETI\n")
    f.write("====================================\n\n")
    f.write("Bu asamada Plant 1 ve Plant 2 anomali verileri Spark DataFrame olarak okunmus,\n")
    f.write("ardindan createOrReplaceTempView kullanilarak SQL ile sorgulanabilir gecici tablolar olusturulmustur.\n\n")
    f.write("Olusturulan tablolar:\n")
    f.write("- plant1_anomaly_table\n")
    f.write("- plant2_anomaly_table\n\n")
    f.write("Spark SQL ile yapilan analizler:\n")
    f.write("- Santral bazli toplam veri ve anomali sayisi\n")
    f.write("- Santral bazli anomali orani\n")
    f.write("- SOURCE_KEY bazinda en cok anomali veren kaynaklar\n")
    f.write("- Gun bazinda anomali yogunlugu\n\n")
    f.write("Bu yapi, yerel ortamda Hive benzeri SQL tabanli buyuk veri analiz katmani olarak kullanilmistir.\n")

print("Kaydedildi:", summary_path)

spark.stop()

print("\nSpark SQL / Hive benzeri analiz tamamlandi.")
