# Analytics Engineering Framework - Orchestration Framework
[Analytics engineers](https://www.getdbt.com/what-is-analytics-engineering) transform, test, deploy, and document data using software engineering principles, providing clean datasets that empower end users to independently answer their own questions.

Data orchestration plays a vital role in enabling efficient data access and analysis, making it critical for data lakes and data warehouses.

This repository provides a streamlined serverless data orchestration framework using Google Cloud Functions. And deployed via Terraform.

Simplify your workflow with automated triggering, scheduling, and reusable business logic executors for BigQuery, Dataproc, and more.

Automate the deployment of your orchestration logic including retry strategy, generic business logic executors, and more.


### 1. CI/CD Pipeline Integration
- Include this repository as a step in your CI/CD pipeline. 
- The CI/CD pipeline seamlessly compiles and deploys Terraform templates, automating the creation of the data orchestration framework's essential infrastructure.

## Integration with Analytics Engineering Framework

This Orchestration Framework is designed as a component of a comprehensive Analytics Engineering Framework comprised of:

1. Analytics Engineering Framework - Data Orchestration: Automates the generation of Google Cloud Workflows Definition files.
2. Analytics Engineering Framework - Orchestration Framework: Seamlessly deploy your orchestration infrastructure.
2. Analytics Engineering Framework - Data Transformation: Houses your data transformation logic.
3. Analytics Engineering Framework - Data Model: Manages data models, schemas and Dataplex lakes and zones.