# Analytics Engineering Framework
[Analytics engineers](https://www.getdbt.com/what-is-analytics-engineering)  lay the foundation for others to organize, transform, and document data using software engineering principles. Providing easy to use data platforms that empower data practitioners to independently build data pipelines in a standardized and scalable way, and answer their own data-driven questions.

![aef_high_level.png](aef_high_level.png)


The Analytics Engineering Framework comprised of:
1. **Orchestration Framework**: Maintained by Analytics Engineers to provide seamless, extensible orchestration and execution infrastructure.
1. **Data Model**: Directly used by end data practitioners to manage data models, schemas, and Dataplex metadata.
1. **Data Orchestration**: Directly used by end data practitioners to define and deploy data pipelines using levels, threads, and steps.
1. **Data Transformation**: Directly used by end data practitioners to define, store, and deploy data transformations.

## Fast deployment in a single project
***Note:*** Production deployments imply careful selection of projects where each component will be deployed. For production adhere to [best practices for establishing robust data foundations](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/blueprints/data-solutions/data-platform-foundations) within these projects.

1. Establish one or more projects (for testing or simplicity, a single project may suffice) where you will deploy the Analytics Engineering Framework. 
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
   - Error Reporting API
   - Cloud Dataproc API
   - Cloud Composer
   - Cloud Data Lineage

```shell
gcloud config set project $1
gcloud services enable bigquery.googleapis.com \
                       bigquerydatapolicy.googleapis.com \
                       bigqueryconnection.googleapis.com \
                       cloudbuild.googleapis.com \
                       storage-component.googleapis.com \
                       cloudresourcemanager.googleapis.com \
                       dataflow.googleapis.com \
                       dataform.googleapis.com \
                       clouderrorreporting.googleapis.com \
                       compute.googleapis.com \
                       servicenetworking.googleapis.com \
                       secretmanager.googleapis.com \
                       firestore.googleapis.com \
                       cloudfunctions.googleapis.com \
                       run.googleapis.com \
                       eventarc.googleapis.com \
                       workflows.googleapis.com \
                       cloudscheduler.googleapis.com \
                       datacatalog.googleapis.com \
                       dataproc.googleapis.com \
                       composer.googleapis.com \
                       datalineage.googleapis.com \
                       clouderrorreporting.googleapis.com
```

3. Clone [aef-data-transformation](), [aef-data-model](), [aef-data-orchestration](), [aef-orchestration-framework]()
5. For demo purposes the demo pipeline runs a Dataform repository, so for that step to work, you need your own Dataform github repository and configure your project names in the Dataform parameters in that repository. Start by making a fork of [this repository](https://github.com/oscarpulido55/aef-sample-dataform-repo.git).
6. Once you have that repository forked, modify it, so it points to the GCP projects where you will deploy / store your data. Modify ***dataform.json*** and push to our own new fork of the sample Dataform repository.
```json
{
 "defaultSchema": "default_dataset",
 "assertionSchema": "dataform_assertions",
 "defaultLocation": "us-central1",
 "warehouse": "bigquery",
 "defaultDatabase": "<PROJECT>",
 "vars": {
   "connection_name": "projects/<PROJECT>/locations/us-central1/connections/sample-connection",
   "dataset_id_landing": "aef_landing_sample_dataset",
   "dataset_projectid_landing": "<PROJECT>",
   "dataset_location_landing": "us-central1",
   "dataset_description_landing": "Landing dataset description",
   "dataset_lake_landing": "aef-sales-lake",
   "dataset_zone_landing": "aef-landing-sample-zone",
   "dataset_id_curated": "aef_curated_sample_dataset",
   "dataset_projectid_curated": "<PROJECT>",
   "dataset_location_curated": "us-central1",
   "dataset_description_curated": "curated dataset description",
   "dataset_lake_curated": "aef-sales-lake",
   "dataset_zone_curated": "aef-curated-sample-zone",
   "dataset_id_exposure": "aef_exposure_sample_dataset",
   "dataset_projectid_exposure": "<PROJECT>",
   "dataset_location_exposure": "us-central1",
   "dataset_description_exposure": "Exposure dataset description",
   "dataset_lake_exposure": "aef-sales-lake",
   "dataset_zone_exposure": "aef-exposure-sample-zone",
   "sample_data_bucket": "<PROJECT>-lnd-sample-data-bucket"
 }
}

```

7. Replace all the references in the four repositories of sample project ***<PROJECT_ID>*** with your projects correspondingly. 
8. Replace all the references in the four repositories of the ***<GITHUB_SPACE>*** by the space where you forked sample Dataform repository in steps 3 to 6.
9. Navigate to each project and deploy terraform resources:

   - For demo only purposes deploy **sample-data** terraform to create a sample PostgreSQL source database, and upload some sample data files to GCS. 
   To be able to run this you should have installed [psql](https://www.postgresql.org/docs/current/app-psql.html)
   Open **demo.tfvars** and set variables to match your projects, regions, etc. Deploy Dataplex metadata and data model:
       ```bash
       cd aef-data-model/sample-data/terraform/
       terraform plan -var-file="demo.tfvars"
       ```
   - Reference some sample Dataform Repositories (already done in sample Terraform vars in repo), so *aef-data-model* can read properties from there to create datasets, add metadata, create BigQuery sample connection, etc. 

   - Open **prod.tfvars** and set variables to match your projects, regions, etc. Deploy Dataplex metadata and data model:
       ```bash
       cd ../../aef-data-model/terraform/
       terraform plan -var-file="prod.tfvars"
       ```
   - Deploy core orchestration framework
       ```bash
       cd ../../aef-orchestration-framework/terraform/
       terraform plan -var 'project=<PROJECT>' -var 'region=us-central1' -var 'operator_email=<EMAIL>'
       ```
   - Open **prod.tfvars** and set variables to match your projects, regions, etc. Deploy data pipelines:
       ```bash
       cd ../../aef-data-orchestration/terraform/
       terraform plan -var-file="prod.tfvars"
       ```
   - Deploy sample data transformation properties definitions (Set DB private IP from DB created in first tep in *sample_jdbc_dataflow_ingestion.json*)
       ```bash
       cd ../../aef-data-transformation/terraform/
       terraform plan -var 'project=<PROJECT>' -var 'region=us-central1' -var 'domain=google' -var 'environment=dev'
       ```
10. Schedule your demo pipeline execution
       ```bash
       cd ../../aef-orchestration-framework/functions/orchestration-helpers/scheduling/utilities/
       sh setup_evn.sh
       sh test_create.sh
       ```