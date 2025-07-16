

# REPO-GROUP-21031-21016-21068-24264: Serverless ETL Pipeline

**Group:** `GROUP-21016-21031-21068-24264`
**Lab ID:** `PROJET-5`
**Owner ID:** `21031`

---

## 🚀 Overview

This repository contains everything you need to deploy a fully-serverless ETL pipeline on AWS:

1. **Extract** raw *consultation* CSV files uploaded to S3
2. **Transform** them to Parquet via AWS Lambda
3. **Load** and catalog with AWS Glue
4. **Query** the results in Athena

All infrastructure is defined with a single CloudFormation template.

---

## 🔄 Transformation Logic (Lambda)

The **transform\_function.py** Lambda is automatically invoked when a new consultation CSV lands in the **Raw S3 Bucket**. It performs the following steps before writing the Parquet output to the **Processed S3 Bucket**:

| Step | Action                                                                                                             |
| ---- | ------------------------------------------------------------------------------------------------------------------ |
| 1    | **Read CSV** from the triggering S3 key using *awswrangler*                                                        |
| 2    | **Parse `date_consultation`** → `datetime`, then derive **`year`** and **`month`** columns                         |
| 3    | **Bucketise `patient_age`** into `age_group` (`enfant`, `adolescent`, `adulte`, `senior`)                          |
| 4    | **Drop rows** where `diagnostic` is `NULL` or empty                                                                |
| 5    | **Rename columns** if present: `id_consultation` → `consultation_id`, `id_centre` → `centre_id`, `sexe` → `gender` |
| 6    | **Write Parquet** file (`same‑key.parquet`) to the processed bucket with Snappy compression                        |
| 7    | **Exit early** if the resulting DataFrame is empty to avoid pointless writes                                       |

The newly created Parquet object triggers the **StartCrawler Lambda**, which launches the Glue Crawler to update the data catalog automatically.

---

## 📂 Repository Structure

```
REPO-GROUP-21031-21016-21068-24264/
├── infrastructure/
│   └── template-etl.yml
├── lambda/
│   ├── transform_function.py
│   └── start-crawler.py
├── diagrams/
│   └── architecture.png               # Full AWS architecture diagram
├── data/
│   └── consultations.csv        # Example consultation CSV

├── README.md
└── .gitignore
```

---

## 🔧 Prerequisites

* AWS CLI v2 configured with sufficient IAM permissions
* Python 3.9+ (for local testing, optional)
* An S3 bucket for raw CSV and one for Athena results
* AWS account with Glue, Athena, Lambda, S3, SNS, SQS, KMS rights

---

## ⚙️ Deployment

1. **Clone the repo**

   ```bash
   git clone git@github.com:<YourUser>/REPO-GROUP-21031-21016-21068-24264.git
   cd REPO-GROUP-21031-21016-21068-24264
   ```

2. **Deploy with CloudFormation**

   ```bash
   aws cloudformation deploy \
     --template-file infrastructure/template-etl.yml \
     --stack-name projet5-etl \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides \
         InputBucketName=projet5-raw-bucket \
         OutputBucketName=projet5-processed-bucket \
         AthenaResultsBucket=projet5-athena-results-bucket \
         OwnerId=21031 \
         GroupId=GROUP-21016-21031-21068-24264 \
         LabId=PROJET-5
   ```

3. **Verify**

   * In the **CloudFormation** console: confirm stack status is **CREATE\_COMPLETE**
   * Check **S3**: raw & processed buckets exist with correct tags
   * Review **IAM**: roles with least-privilege policies

---

## 🧪 Testing the Pipeline

Follow these **sequential commands**, one step at a time:

---

### 1 – Upload the dataset to the raw bucket

```bash
aws s3 cp data/consultations.csv s3://projet5-raw-bucket/consultations.csv
```

Verify in the S3 console (Raw bucket) that the object is present.

---

### 2 – Watch the Lambda transform in real time

```bash
aws logs tail /aws/lambda/projet5-etl-21031-csv-to-parquet --since 1m --follow
```

You should see a log line like:

```
Transformé : consultations.parquet (… lignes)
```

---

### 3 – Confirm the Parquet file in the processed bucket

```bash
aws s3 ls s3://projet5-processed-bucket/ --recursive | grep consultations.parquet
```

Expect a single `.parquet` object.

---

### 4 – Check Glue Crawler state

```bash
aws glue get-crawler \
  --name projet5-etl-21031-crawler \
  --query 'Crawler.State' --output text
```

Value should switch from `RUNNING` to `READY` once catalog update is complete.

---

### 5 – Launch an Athena query

```bash
aws athena start-query-execution \
  --work-group projet5-etl-21031-workgroup \
  --query-string "SELECT age_group, COUNT(*) AS cnt \
    FROM \"projet5-etl-21031-etl_db\".projet5_processed_bucket \
    GROUP BY age_group;" \
  --query-execution-context Database=projet5-etl-21031-etl_db \
  --result-configuration OutputLocation=s3://projet5-athena-results-bucket/
```

Note the `QueryExecutionId` returned.

---

### 6 – Fetch the query results

```bash
aws athena get-query-results --query-execution-id <QueryExecutionId>
```

You should see row counts per `age_group`.

---

### 7 – Locate the results file in the Athena bucket

```bash
aws s3 ls s3://projet5-athena-results-bucket/ --recursive | head
```

The CSV/JSON result file for the query is stored here.

---

### 8 – Trigger the DLQ to test alerting

Upload an empty or malformed CSV:

```bash
aws s3 cp bad.csv s3://projet5-raw-bucket/bad.csv
```

After a few minutes, check the DLQ metric or SQS queue:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=<OwnerId>-etl-dlq \
  --start-time $(date -u -d '-10 minutes' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time   $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 --statistics Sum
```

An SNS e‑mail alert should arrive because the DLQ now contains ≥ 1 message.

> The examples already contain the stack name `projet5-etl`; replace only the bucket/workgroup names where indicated.

---

## 🔐 Security & Tags

* **Encryption:** SSE-KMS on all S3 buckets & Athena results
* **Tags** on every resource:

  * `supnum:Lab = PROJET-5`
  * `supnum:Group = GROUP-21016-21031-21068-24264`
  * `supnum:Owner = 21031`

---

## 📈 Monitoring

* **CloudWatch Alarms** on Lambda Errors & Duration, **and on DLQ message count (ApproximateNumberOfMessagesVisible) — you’ll get an email as soon as at least one message is waiting**
* **SNS Topic** aggregates alerts → email subscription

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Commit your changes (`git commit -m "feat: ..."`)
4. Push to your branch and open a Pull Request

---

## 📝 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
