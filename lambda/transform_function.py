import os, json, awswrangler as wr, pandas as pd

OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']

def lambda_handler(event, context):
    print("DEBUG_EVENT:", json.dumps(event))
    for rec in event['Records']:
        src = rec['s3']['bucket']['name']
        key = rec['s3']['object']['key']
        df = wr.s3.read_csv(f"s3://{src}/{key}")

        df['date_consultation'] = pd.to_datetime(df['date_consultation'], format='%Y-%m-%d')
        df['year']  = df['date_consultation'].dt.year
        df['month'] = df['date_consultation'].dt.month
        bins, labels = [0,12,18,65,200], ['enfant','adolescent','adulte','senior']
        df['age_group'] = pd.cut(df['patient_age'], bins=bins, labels=labels, right=False)

        df = df.dropna(subset=['diagnostic'])
        for old, new in [
            ('id_consultation','consultation_id'),
            ('id_centre','centre_id'),
            ('sexe','gender')
        ]:
            if old in df.columns:
                df = df.rename(columns={old:new})

        if df.empty:
            print("DEBUG: no rows to process, exiting")
            return

        dst = key.replace('.csv','.parquet')
        wr.s3.to_parquet(df=df, path=f"s3://{OUTPUT_BUCKET}/{dst}", dataset=False)
        print(f"Transformé : {dst} ({len(df)} lignes)")
