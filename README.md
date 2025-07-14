# REPO-GROUP-21031-21016-21068-24264: Serverless ETL Pipeline

**Group:** `GROUP-21016-21031-21068-24264`
**Lab ID:** `PROJET-5`
**Owner ID:** `21031`

---

## 🚀 Overview

This repository contains everything you need to deploy a fully-serverless ETL pipeline on AWS:

1. **Extract** raw CSV files uploaded to S3
2. **Transform** them to Parquet via AWS Lambda
3. **Load** and catalog with AWS Glue
4. **Query** the results in Athena

All infrastructure is defined with a single CloudFormation template.

---

## 📂 Repository Structure

```
REPO-GROUP-21031-21016-21068-24264/
├── infrastructure/
│   └── template-etl.yml               # CloudFormation template
├── lambda/
│   ├── transform_function.py          # Lambda CSV→Parquet code
│   └── start-crawler.py               # Lambda to start the Glue Crawler
├── diagrams/
│   └── architecture.png               # Full AWS architecture diagram
├── README.md                          # (this file)
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
         InputBucketName=<your-raw-bucket> \
         OutputBucketName=<your-processed-bucket> \
         AthenaResultsBucket=<your-athena-results-bucket> \
         OwnerId=21031 \
         LabId=PROJET-5 \
         GroupId=GROUP-21016-21031-21068-24264
   ```

3. **Verify**

   * In the **CloudFormation** console: confirm stack status is **CREATE\_COMPLETE**
   * Check **S3**: raw & processed buckets exist with correct tags
   * Review **IAM**: roles with least-privilege policies

---

## 🧪 Testing the Pipeline

1. **Upload** a sample CSV to your raw S3 bucket:

   ```bash
   aws s3 cp sample.csv s3://<your-raw-bucket>/sample.csv
   ```
2. **Monitor** the Lambda logs in CloudWatch for transformation output.
3. **Inspect** the processed Parquet file in the processed S3 bucket.
4. **Run** an Athena query (in the `projet5-etl_*` database) to validate data, for example:

   ```sql
   SELECT age_group, COUNT(*) AS cnt
   FROM "projet5-etl-21031-etl_db".supnum_processed_21031
   GROUP BY age_group;
   ```

---

## 🔐 Security & Tags

* **Encryption:** SSE-KMS on all S3 buckets & Athena results
* **Tags** on every resource:

  * `supnum:Lab = PROJET-5`
  * `supnum:Group = GROUP-21016-21031-21068-24264`
  * `supnum:Owner = 21031`

---

## 📈 Monitoring

* **CloudWatch Alarms** on Lambda Errors & Duration
* **EventBridge Rules** for S3 events, Lambda failures, Glue crawler & Athena query state
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
