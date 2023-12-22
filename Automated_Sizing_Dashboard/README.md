# LE Automated Sizing Dashboard

a web application where it helps to track or audit the instance types currently set to most customer deployments. Instances would connect to this dashboard to query their designated instance type and if not set properly, they will be resized according to what was defined in the dashboard.

## Dependencies

### Tools
1. Python 3.8.13
2. HTML
3. JavaScript
4. Ajax
### Libraries
1. Python Flask
2. Flask-AWSCognito
3. Python Requests
4. Boto3
5. bson
6. Standard Python Libraries
### Services
#### In-App
1. AWS DynamoDB
2. AWS Parameter Store (SSM)
3. Amazon Cognito
4. AWS S3
5. JIRA
#### Deployment (To be used when deploying the application in AWS)
1. AWS Elastic Load Balancer
2. AWS Fargate
3. AWS Elastic Container Registry
4. AWS Route53
5. AWS Web Application Firewall

© 2023 Clark Pañares.