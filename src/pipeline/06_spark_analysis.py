from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, max as spark_max, to_date

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "solar_data"
OUTPUT_DIR = PROJECT_DIR / "spark_outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

spark = SparkSession.builder \
    .appName("GES Spark Anomaly Analysis") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

def read_csv(path):
    return spark.read.option("header", True).option("inferSchema", True).csv(str(path))

def save_with_pandas(spark_df, output_file):
    pdf = spark_df.toPandas()
    pdf.to_csv(output_file, index=False, encoding="utf-8-sig")
    print("Kaydedildi:", output_file)

print("Spark analizi basladi...")

plant1 = read_csv(DATA_DIR / "Plant_1_Anomaly_Data.csv")
plant2 = read_csv(DATA_DIR / "Plant_2_Anomaly_Data.csv")

print("\nPlant 1 satir sayisi:", plant1.count())
print("Plant 2 satir sayisi:", plant2.count())

plant1_anom = plant1.filter(col("ANOMALY") == True)
plant2_anom = plant2.filter(col("ANOMALY") == True)

print("\nPlant 1 anomali sayisi:", plant1_anom.count())
print("Plant 2 anomali sayisi:", plant2_anom.count())

p1_source = plant1_anom.groupBy("SOURCE_KEY") \
    .agg(
        count("*").alias("ANOMALY_COUNT"),
        avg("POWER_GAP").alias("AVG_POWER_GAP"),
        spark_max("POWER_GAP").alias("MAX_POWER_GAP")
    ) \
    .orderBy(col("ANOMALY_COUNT").desc())

p2_source = plant2_anom.groupBy("SOURCE_KEY") \
    .agg(
        count("*").alias("ANOMALY_COUNT"),
        avg("POWER_GAP").alias("AVG_POWER_GAP"),
        spark_max("POWER_GAP").alias("MAX_POWER_GAP")
    ) \
    .orderBy(col("ANOMALY_COUNT").desc())

p1_day = plant1_anom.withColumn("DATE", to_date(col("DATE_TIME"))) \
    .groupBy("DATE") \
    .agg(count("*").alias("ANOMALY_COUNT")) \
    .orderBy(col("ANOMALY_COUNT").desc())

p2_day = plant2_anom.withColumn("DATE", to_date(col("DATE_TIME"))) \
    .groupBy("DATE") \
    .agg(count("*").alias("ANOMALY_COUNT")) \
    .orderBy(col("ANOMALY_COUNT").desc())

print("\nPlant 1 en cok anomali veren SOURCE_KEY:")
p1_source.show(10, truncate=False)

print("\nPlant 2 en cok anomali veren SOURCE_KEY:")
p2_source.show(10, truncate=False)

print("\nPlant 1 gun bazli anomali:")
p1_day.show(10, truncate=False)

print("\nPlant 2 gun bazli anomali:")
p2_day.show(10, truncate=False)

save_with_pandas(p1_source, OUTPUT_DIR / "plant1_anomaly_by_source_spark.csv")
save_with_pandas(p2_source, OUTPUT_DIR / "plant2_anomaly_by_source_spark.csv")
save_with_pandas(p1_day, OUTPUT_DIR / "plant1_anomaly_by_day_spark.csv")
save_with_pandas(p2_day, OUTPUT_DIR / "plant2_anomaly_by_day_spark.csv")

spark.stop()

print("\nSpark analizi tamamlandi.")
print("Sonuclar spark_outputs klasorune kaydedildi.")
