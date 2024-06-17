# Analytics Engineering Framework
[Analytics engineers](https://www.getdbt.com/what-is-analytics-engineering)  lay the foundation for others to organize, transform, and document data using software engineering principles. Providing easy to use data platforms that empower data practitioners to independently build data pipelines in a standardized and scalable way, and answer their own data-driven questions.

![aef_high_level.png](aef_high_level.png)


The Analytics Engineering Framework comprised of:
1. **Orchestration Framework**: Maintained by Analytics Engineers to provide seamless, extensible orchestration and execution infrastructure.
1. **Data Model**: Directly used by end data practitioners to manage data models, schemas, and Dataplex metadata.
1. **Data Orchestration**: Directly used by end data practitioners to define and deploy data pipelines using levels, threads, and steps.
1. **Data Transformation**: Directly used by end data practitioners to define, store, and deploy data transformations.

## Fast deployment for demo or learning purposes 
1. Establish one or more projects (for testing or simplicity, a single project may suffice) where you will deploy the Analytics Engineering Framework. For production adhere to [best practices for establishing robust data foundations](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/blueprints/data-solutions/data-platform-foundations) within these projects.
2. Enable required Google Cloud APIs in your projects.
   - — 
   - BigQuery Connection API 
   - BigQuery Data Policy API 
   - Dataform API 
   - Error Reporting API 
   - — 
   - Compute Engine API 
   - Service Networking API 
   - — 
   - Secret Manager API 
   - — 
   - Google Cloud Firestore API 
   - Cloud Functions API 
   - Cloud Run Admin API 
   - Cloud Build API 
   - Eventarc API 
   - Workflows API
   - — 
   - Cloud Scheduler API 
   - Dataflow API
3. Clone [aef-data-transformation](), [aef-data-model](), [aef-data-orchestration](), [aef-orchestration-framework]()
4. Replace all the references in the four repositories of sample project ***analytics-engg-framework-demo*** with your projects correspondingly. 
5. Navigate to each project and deploy terraform resources:

   - For demo only purposes deploy *sample-data* terraform to create a sample PostgreSQL source database, and upload some sample data files to GCS.
       ```bash
       cd aef-data-model/sample-data/terraform/
       terraform plan -var-file="demo.tfvars"
       ```
   - Reference some sample Dataform Repositories (already done in sample Terraform vars in repo), so *aef-data-model* can read properties from there to create datasets, add metadata, create BigQuery sample connection, etc. 

   - Deploy Dataplex metadata and data model
       ```bash
       cd ../../aef-data-model/terraform/
       terraform plan -var-file="prod.tfvars"
       ```
   - Deploy core orchestration framework
       ```bash
       cd ../../aef-orchestration-framework/terraform/
       terraform plan -var 'project=<PROJECT>' -var 'region=us-central1' -var 'operator_email=<EMAIL>'
       ```
   - Deploy sample data pipelines
       ```bash
       cd ../../aef-data-orchestration/terraform/
       terraform plan -var 'project=<PROJECT>' -var 'data_transformation_project=<PROJECT>' -var 'environment=dev' -var 'region=us-central1' -var 'deploy_cloud_workflows=true' 
       ```
   - Deploy sample data transformation properties definitions (Set DB private IP from DB created in first tep in *sample_jdbc_dataflow_ingestion.json*)
       ```bash
       cd ../../aef-data-transformation/terraform/
       terraform plan -var 'project=<PROJECT>' -var 'region=us-central1' -var 'domain=google' -var 'environment=dev'
       ```
6.  Schedule your demo pipeline execution
       ```bash
       cd ../../aef-orchestration-framework/functions/orchestration-helpers/scheduling/utilities/
       sh setup_evn.sh
       sh test_create_demo.sh
       ```