# Analytics Engineering Framework - Orchestration Framework
[Analytics engineers](https://www.getdbt.com/what-is-analytics-engineering)  lay the foundation for others to organize, transform, and document data using software engineering principles. Providing easy to use data platforms that empower data practitioners to independently build data pipelines in a standardized and scalable way, and answer their own data-driven questions.

Data orchestration plays a vital role in enabling efficient data access and analysis, this repository deploys the core artifacts of a streamlined serverless data orchestration framework using generic executors as Google Cloud Functions. And deployed via Terraform.

This Orchestration Framework is the core integrator of the Analytics Engineering Framework comprised of:
1. **(This repository) Orchestration Framework**: Maintained by Analytics Engineers to provide seamless, extensible orchestration and execution infrastructure.
1. **Data Model**: Directly used by end data practitioners to manage data models, schemas, and Dataplex metadata.
1. **Data Orchestration**: Directly used by end data practitioners to define and deploy data pipelines using levels, threads, and steps.
1. **Data Transformation**: Directly used by end data practitioners to define, store, and deploy data transformations.

### Concepts
#### Cloud Workflows Orchestration implementation:
When seeking a cost-effective and fully serverless orchestration solution for your Google Cloud Platform (GCP) data pipelines, Cloud Workflows emerges as a compelling alternative to Airflow/Composer.
- **Serverless Simplicity**: Eliminate the need to manage servers or GKE clusters at all, completely managed auto scalable serverless service.
- **No Software Tuning Required**: Avoid the complexities of configuring Airflow or Composer parameters for scaling (make composer scale to support more DAGs) or performance optimization (make Composer scale to support more concurrent tasks). No parameters to care about in Cloud Workflows, deploy and forget.
- **Zero Code**: Define your workflows using simple YAML files stored directly within Cloud Workflows.
- **Cost-Efficiency**: Take advantage of 5,000 free steps per month per project, often sufficient for most data platforms, especially with a decentralized approach. Additional steps are billed at a mere $0.01 USD per 1,000 steps. External API calls are priced separately (2,000 free/month, then $0.025 USD per 1,000).
- **Seamless GCP Integration**: Cloud Workflows seamlessly integrates with other GCP services, making it easy to incorporate tasks like BigQuery queries, Cloud Functions executions, and interactions with various Google Cloud APIs into your pipelines.
- **External API Connectivity**: Extend your workflow capabilities by effortlessly calling external APIs, enabling integration with third-party services and data sources.
 
After deploying data pipelines (levels, threads, and steps) as Cloud Workflows within a GCP project (typically using the data orchestration repository), each workflow step will reference a corresponding Cloud Function. These Cloud Functions must be able to interpret parameter files from the data transformation repository and execute tasks accordingly. The repository already contains execution examples like the Dataform tag executor, the Dataflow flex templates executor and the BigQuery saved Query executor, and you can define new, similar Cloud Functions for additional use cases. Ensure these functions are designed to be extensible and reusable across various jobs.

Furthermore, to facilitate operation and debugging, BigQuery tables storing orchestration metadata will be utilized. These tables will serve as a supplementary observability layer, providing insights beyond Cloud Logging and Cloud Monitoring.
![orchestration_implementation.png](orchestration_implementation.png)

#### Scheduling and execution
To trigger Workflows, this streamlined execution approach leverages cron-based schedules defined as Cloud Scheduler rules. This allows for the storage and easy manipulation of scheduling definitions outside of the repository. You can change the frequency or execution time independently of the actual data pipeline definition, without requiring any repository commits or CI/CD processes. Simply insert or update a record in a Firestore configuration table. From there, an event-driven mechanism based on Eventarc and Cloud Functions will create or update the Cloud Scheduler accordingly.
![scheduling_implementation.png](scheduling_implementation.png)

### Repository
This repository defines and deploy the core components for data pipelines orchestration strategy leveraging Cloud Workflows for data pipeline definition and Cloud Functions for serverless execution.
```
├── functions
    ├── data-processing-engines
    │   ├── bq-saved-query-executor     
    │   ├── dataflow-flextemplate-job-executor
    │   ├── dataform-tag-executor
    │   ├── dataproc-serverless-executor
    │   └── ... 
    └── orchestration-helpers
        ├── intermediate
        ├── pipeline-executor
        ├── scheduling
        └── ...
```

## Usage
### Terraform
1. Define your terraform variables
<!-- BEGIN TFDTFOC -->
| name                                         | description                                                                                                                                                                                                                 | type                                               | required | default                                 |
|-----------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|----------|-------------------------------------------|
| [project](variables.tf#L11)                  | Project ID where the AEF Orchestration Framework will be deployed.                                                                                                                                                            | string                                                 | true     | -                                        |
| [region](variables.tf#L17)                   | Name of the region for the components to be deployed                                                                                                                                                                       | string                                                 | true     | -                                        |
| [operator_email](variables.tf#L23)           | email of the data platform operator for error notifications                                                                                                                                                                     | string                                                 | true     | -                                        |
| [workflows_scheduling_table_name](variables.tf#L29) | workflows scheduling table name                                                                                                                                                                                                     | string                                                 | true     | workflows_scheduling                      |
<!-- END TFDOC -->

2. Run the Terraform Plan / Apply using the variables you defined.
```bash
terraform plan -var 'project=<PROJECT>' -var 'region=<REGION>' -var 'operator_email=<EMAIL>'
```