# LE Test Environments Dashboard

An internal tool that lets the team to manage and monitor all the test environments they are using for any tasks. This is to prevent two or more users using the same test environment in the same time which can cause inaccurate results of the test due to one of the users might affecting other user's testing.

## Logging

1. Stored inside the application (logs/access.log) although it may not be possible to access it since it is deployed to Fargate.
2. Stored in CloudWatch
3. Actions taken in the application are shown in the Reports tab (also in the application) for 90 days before it gets deleted. It is being handled by DynamoDB TTL feature.

© 2022 Clark Pañares.