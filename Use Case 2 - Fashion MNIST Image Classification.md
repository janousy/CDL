# Use Case 2 - Fashion MNIST Image Classification

This use case trains and deploys an image classification model, based on the Fashion MNIST dataset provided by Zalando AG available at the official Zalando [research repository](https://github.com/zalandoresearch/fashion-mnist). 

## Data Pipeline

For this use case, we simplify the data pipeline by ingesting the provided Fashion MNIST dataset into two buckets for training and testing. The complete pipeline would have the same architecture as the one for the BBC News dataset.

```sql
# create the repositories for the raw dataset
pachctl create repo fmnist-train-raw
pachctl create repo fmnist-test-raw

# navigate to the downloaded dataset
pachctl put file -r fmnist-test-raw@master:/ -f fmnist-test-raw
pachctl put file -r fmnist-train-raw@master:/ -f fmnist-train-raw
```

## Model Pipeline

```sql
# create a socks proxy such that the Kubernetes cluster can be reached
export http_proxy=socks5://127.0.0.1:9999

# set the IP according to your LoadBalancerIP of the Determined AI master
export DET_MASTER=http://10.64.140.43:8080/

# now you can run your experiment
cd fmnist/model/src
# perform a hyperparameter tuning experiment
det experiment create -f adaptive.yaml .
# perform a single training experiment
det experiment create -f const.yaml .
```

- To register a model, perform the following steps:

```bash
det model list

export MODEL_NAME=fashion-classifier

# only if this is the first iteration, create a new model
det model create $MODEL_NAME

# look up checkpoint uuid in the Determined UI
det model register-version $MODEL_NAME <checkpoint_uuid>

det model describe $MODEL_NAME
det model list-versions $MODEL_NAME
```

- After registering a new model version, you can push your code to the repository. In this case, the last submitted experiment corresponds to code locally. If the registered checkpoint wasn't not produced by the last submitted experiment, the local code has to be adjusted, e.g. by downloading the model artifacts and replacing the model code.
- The GitLab pipeline will trigger and test the new model version. The python test `fmnist/test/test_model_accuracy.py` loads the model artifacts from the DeterminedAI registry together with the test dataset. A report will be produced as a pipeline artifact that lists the model versions and their metadata, which includes the test results.

## Deployment Pipeline

The deployment is solely performed through a GitLab pipeline on the `master` branch only:

- The model wrapper loads the model artifacts from DeterminedAI, including its dependencies such as the vocabulary and the classes.
- A build-step builds and pushes a Docker image for the Seldon micro-service , using the model wrapper `bbc/deploy/NewsModel.py` defined to perform predictions.
- Another GitLab job then deploys the wrapped model to the Kubernetes cluster, using the deployment manifest `bbc/deploy/deploy.yaml` .

Seldon exposes a Swagger API documentation, where we can test our endpoint:

```sql
kubectl get svc istio-ingressgateway -n istio-system

http://<EXTERNAL-IP>/seldon/<namespace>/<model-name>/api/v1.0/doc/
# visiti the address on your browser
http://10.64.140.45/seldon/default/fashion-classifier/api/v1.0/doc/
```

We can then send a JSON-request to the endpoint at `/seldon/default/fasion-classifier/api/v1.0/predictions` .

- There is currently an issue when serving Tensorflow models with Seldon, described in this [Github issue](https://github.com/keras-team/keras/issues/6462) and on [Stackoverflow](https://stackoverflow.com/questions/54652536/keras-tensorflow-backend-error-tensor-input-10-specified-in-either-feed-de). The issue has not yet been resolved in this use case.

```sql
{
  "data": {
    "names": [
      "feature1"
    ],
    "tensor": {
      "shape": [
        28,
        28
      ],
      "values": [[ # random 28x28 array]]
    }
  }
}
```

- for the values, you can for example use one of the test images provided by the keras dataset:

```bash
import tensorflow 
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.fashion_mnist.load_data()
x_test[0]
```