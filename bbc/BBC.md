# Use Case 1 - BBC News Text Classification

This use case trains and deploys a text classification model, based on the BBC News dataset available at [http://mlg.ucd.ie/datasets/bbc.html](http://mlg.ucd.ie/datasets/bbc.html).

The source code compromises the `.gitlab-ci.yml` CI/CD pipeline and a main folder with three subdirectories for the `data`, `model` and `deploy` pipeline. Additionally, a `test` folder includes the scripts to evaluate the current model. Create a new GitLab repository and upload the content related to this use case.

## Data Pipeline

### Postgres

[https://www.postgresql.org/](https://www.postgresql.org/)

- Within Postgres, set up a user `postgres` (created by default) and set the password to `postgres`
- If you choose a different username and password, adjust the credentials within the files `bbc/data/pipeline/label/write_db.py` and `bbc/model/src/data.py` accordingly.
- Set up a database `bbc-news`, and create two tables:

```sql
CREATE TABLE IF NOT EXISTS bbc_test (
	LABEL_ID integer PRIMARY KEY,
	LABEL VARCHAR (100)  NOT NULL,
	FILEPATH VARCHAR (200) NOT NULL UNIQUE,
	CREATOR_MAIL VARCHAR (100),
	LABEL_CREATE_DATE TIMESTAMP,
	BRANCH VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS bbc_train (
  LABEL_ID integer PRIMARY KEY,
  LABEL VARCHAR (100)  NOT NULL,
  FILEPATH VARCHAR (200) NOT NULL UNIQUE,
	CREATOR_MAIL VARCHAR (100),
	LABEL_CREATE_DATE TIMESTAMP,
	BRANCH VARCHAR(200)
);
```

### Pachyderm

[https://www.pachyderm.com/](https://www.pachyderm.com/)

In this use case, the Pachyderm Enterprise edition was used, which is activated until the end of the year 2021. If you choose to use the Community edition, you will be able to reproduce everything performed in this use case, but you cannot directly ingest data from repositories into LabelStudio, as the S3 gateway is not exposed.

- Download the raw bbc-news dataset from the following link: [http://mlg.ucd.ie/files/datasets/bbc-fulltext.zip](http://mlg.ucd.ie/files/datasets/bbc-fulltext.zip).
- The dataset is initially split. To generate a test and train dataset, run the script `bbc/data/prepare/bbc-generate-dataset.py`, whereby you have to adjust the paths according to your needs.
- Then create the pachyderm repositories and pipelines. The created pipelines clean & validate the news articles, and ingest labels into the database.

```bash
# create the repositories for the raw dataset
pachctl create repo bbc-train-raw
pachctl create repo bbc-test-raw

# navigate to the dataset generated with the script
# this will run for some minutes
pachctl put file -r bbc-test-raw@master:/ -f bbc-test-raw
pachctl put file -r bbc-train-raw@master:/ -f bbc-train-raw

cd bbc/data/pipeline/validate
pachctl create pipeline -f bbc-test-validate.json
pachctl create pipeline -f bbc-train-validate.json

# create the labels
pachctl create repo bbc-test-label
pachctl create repo bbc-train-label

pachctl put file -r bbc-test-label@master:/ -f bbc-test-label
pachctl put file -r bbc-train-label@master:/ -f bbc-train-label

cd bbc/data/pipeline/label
pachctl create pipeline -f bbc-test-store-label.json
pachctl create pipeline -f bbc-train-store-label.json
```

- Each dataset - test and train - share a Docker image `bbc/data/pipeline/Dockerfile` that includes the code executed by the pipeline for both steps - validation and storing labels. The Docker image is built and pushed by the GitLab pipeline upon a push to the repository.

### LabelStudio

[https://labelstud.io/](https://labelstud.io/)

In this use case, we do not label our data manually using LabelStudio, but you can ingest the validated data through the S3 gateway exposed by the Pachyderm Enterprise edition for each repository.

- To connect LabelStudio to a Pachyderm repository, look into the installation instructions of LabelStudio.

## Model Pipeline

[https://www.determined.ai/](https://www.determined.ai/)

DeterminedAI allow to remotely execute experiments on a Kubernetes cluster. The experiments run containerized using default images from DeterminedAI by default. To add additional dependencies, you can either use a startup script `startup-hook.sh` or create a Docker image and specify the environment within the experiment configuration. In our use cases, we work with Docker images.

- To run the experiment, use the `det` CLI for remote execution.

```bash
# create a socks proxy such that the Kubernetes cluster can be reached
pip install pysocks
export http_proxy=socks5://127.0.0.1:9999

# set the IP according to your LoadBalancerIP of the Determined AI master
export DET_MASTER=http://10.64.140.43:8080/

# now you can run your experiment
cd bbc/model/src
# perform a hyperparameter tuning experiment
det experiment create -f adaptive.yaml .
# perform a single training experiment
det experiment create -f const.yaml .
```

- To register a model, perform the following steps:

```bash
det model list

export MODEL_NAME=news-classifier

# only if this is the first iteration, create a new model
det model create $MODEL_NAME

# look up checkpoint uuid in the Determined UI
det model register-version $MODEL_NAME <checkpoint_uuid>

det model describe $MODEL_NAME
det model list-versions $MODEL_NAME
```

- After registering a new model version, you can push your code to the repository. In this case, the last submitted experiment corresponds to code locally. If the registered checkpoint was not produced by the last submitted experiment, the local code has to be adjusted, e.g. by downloading the model artifacts and replacing the model code via the determined CLI.
- The GitLab pipeline will trigger and test the new model version. The python test `bbc/test/test_model_accuracy.py` loads the model artifacts from the DeterminedAI registry and a test dataset.  A report will be produced as a pipeline artifact that lists the model versions and their metadata, which includes the test results.

## Deployment Pipeline

The deployment is solely performed through a GitLab pipeline on the `master` branch only:

- The model wrapper loads the model artifacts from DeterminedAI, including its dependencies such as the vocabulary and the classes.
- A build-step builds and pushes a Docker image for the Seldon micro-service, using the model wrapper `bbc/deploy/NewsModel.py` defined to perform predictions.
- Another GitLab job then deploys the wrapped model to the Kubernetes cluster, using the deployment manifest `bbc/deploy/deploy.yaml`.

Seldon exposes a Swagger API documentation, where we can test our endpoint:

```sql
kubectl get svc istio-ingressgateway -n istio-system

http://<EXTERNAL-IP>/seldon/<namespace>/<model-name>/api/v1.0/doc/
# visiti the address on your browser
http://10.64.140.45/seldon/default/news-classifier/api/v1.0/doc/
```

We can then send a JSON-request to the endpoint to `http://<EXTERNAL-IP>/seldon/default/news-classifier/api/v1.0/predictions`

```sql
{
  "data": {
    "names": [
      "feature1"
    ],
    "tensor": {
      "shape": [
        1,
        1
      ],
      "values": [
        "Northern Irishman Rea, who won his 100th race on Saturday, held off the early challenge of Ducati's Scott Redding to win in damp conditions."
      ]
    }
  }
}

```