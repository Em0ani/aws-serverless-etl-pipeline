import os, boto3
def lambda_handler(event, context):
    crawler = os.environ['CRAWLER_NAME']
    boto3.client('glue').start_crawler(Name=crawler)
