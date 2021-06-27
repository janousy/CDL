# Setup

This document will walk through the required installation to apply the uses cases. The technologies listed here were used to develop the prototype, however alternatives are applicable. All the technologies used are available open-source or at least free.

# Requirements

The following underlying hardware on OpenStack was used to install the required software:

- Virtual Machine (VM) - *CUDA 10.2 on Ubuntu 18.04 - 32cpu-128ram-hpcv3-gpuT4*
    - This machine is required to have at least on GPU, with drivers preinstalled, otherwise you will not be able to run experiments on Kubernetes.
    - 32 CPUs and 128 GB Ram is recommended, although 16 CPUs with 64 Ram might be sufficient
- (Optional) Virtual Machine (VM) *- Ubuntu 18.04 - 2cpu-8ram-hpcv3*
    - This machine is used to host the GitLab installation, it does not require a GPU
    - You can also run GitLab on the same machine that host other services.

**VM IMAGES:**

- If you have access to the UZH Science Cloud and the *gall.ifi.uzh* project, you can use a pre-installed setup with the following images. The default credentials can be found at the end of this document.
    - `jabalt-cdl-gpu-20210624`
    - `jabalt-gitlab-20210624`

For local development, macOS 11.2.3 was used. If you prefer to use a different operating system locally, you may have to adapt the installation steps.

You further need:

- An image registry for the Docker images of the use cases, in our case we used DockerHub ([https://hub.docker.com/](https://hub.docker.com/)). You may also use the registry provided by GitLab for better performance.
- Basic knowledge of Docker and Kubernetes

### Ports

The following ingress ports need to opened on the large VM. If you have access to the `gall.ifi.uzh` project on ScienceCloud, you can use the `jabalt_mlflow` security group.

- 80 - HTTP Traffic
- 650 - Pachyderm Client (pachd)
- 5432 - Postgres
- 8000 - Determined AI CLI and Seldon REST API
- 8080 - Determined AI Dashboard
- 9000 - Minio Object Storage and Seldon REST API
- 9999 - SSH Port (see Network Setup)
- 10001 - Determined AI
- 10443 - General TCP/UDP traffic
- 16443 - Kubernetes API
- 30080 - Pachyderm Web UI
- 30650 - Pachyderm

## Local Installations

- Helm v3.5.4 ([installation](https://helm.sh/docs/intro/install/))
- Kubectl v1.17.17 ([installation](https://kubernetes.io/de/docs/tasks/tools/install-kubectl/))
- Python 3.7 (we recommend a virtual environment, e.g. [Anaconda](https://www.anaconda.com/))

## Network Setup

- The VMs were accessed through a VPN. We recommend using a Socks5 proxy, such that at least HTTP traffic is routed through the VPN and you can access services on the Kubernetes cluster (the cluster will probably not have a public IP). To do so on macOS, visit the VPN settings in the network preferences and under `Advanced/Proxies`, set up a Socks Proxy Server at `127.0.0.1` with port `9999` (you can choose any free port here, however you need to open the port on the VM)
- When setting up an SSH connection to the VM, specify the chosen port above, e.g. `ssh -i ~/.ssh/id_rsa -q -D9999 ubuntu@172.23.76.93`

# Kubernetes

To facilitate a convenient installation of Kubernetes, Ubuntu's [Microk8s](https://microk8s.io/docs) 1.20 was used. It provides a single-node development cluster with useful add-ons. It is not recommended using a newer version, as issues with GPU utilization may arise (at the time of this thesis)

- Install Microk8s 1.20 on Ubuntu ([https://microk8s.io/docs](https://microk8s.io/docs))

```bash
sudo snap install microk8s --classic --channel=1.20

# join user group
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube

# create an alias for kubectl
sudo snap alias microk8s.kubectl kubectl

# create a kubectl config file
sudo microk8s config > ~/.kube/config
```

- Install `kubectl` locally using these instructions [here](https://kubernetes.io/de/docs/tasks/tools/install-kubectl/).
- Then configure access to the cluster from your local machine:
    - Create a local configuration file: `~/.kube/config`
    - Run the command `microk8s config` on the host machine
    - Copy the output into the local configuration file
    - Test the connection with `kubectl describe node`

## Enable Add-Ons

Further, configure your cluster by following the instructions below.

```bash
# the basics
sudo microk8s enable dns storage dashboard

# setup GPU access
sudo microk8s enable gpu

# enable LoadBalancer IPs 
microk8s enable metallb:10.64.140.43-10.64.140.49
microk8s enable host-access

# to get istio and allow model serving
microk8s enable knative
```

# Storage

To store deep learning data sets, model artifacts etc., an S3 compatible object storage as well as a database is required. For object storage, we chose Minio, as it is a recommended S3 compatible, Kubernetes native object storage that can be deployed on-premise. As a database, our tool of choice is Postgres.

## Install Minio

[https://min.io/](https://min.io/)

Version: 2021-04-22T15:44:28Z

You can follow [these installation](https://www.digitalocean.com/community/tutorials/how-to-set-up-an-object-storage-server-using-minio-on-ubuntu-18-04-de) instructions to install Minio on Ubuntu 18.04. For accessibility reasons, the Minio instance is not deployed to Microk8s, although being an option. The web UI can be access at `http://<VM-IP>:9000/`

## Install Postgres

[https://www.postgresql.org/](https://www.postgresql.org/)

Version: 10

You can follow [these installation](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04-de) instructions to install Postgres o Ubuntu 18.04. You will need to make a few minor adjustments to be able to reach the Database from your local machine. If you want to do so, apply the following changes:

```bash
export $PG_VERSION = 10
sudo nano /etc/postgresql/$PG_VERSION/main/postgresql.conf

# change the listen address to
listen_addresses = '*'

sudo nano /etc/postgresql/$PG_VERSION/main/pg_hba.conf

#add the following line
host  all  all 0.0.0.0/0 md5
```

# Pachyderm

[https://docs.pachyderm.com/latest/](https://docs.pachyderm.com/latest/)
Version 1.13.2

We use Pachyderm for the data pipeline. Make sure you have `kubectl` configured locally, then install the Pachyderm CLI on your local machine:

- We used `pachctl` and `pachd` version 1.13.2
- You can find the official installation instructions [here](https://docs.pachyderm.com/latest/getting_started/local_installation/#install-pachctl).

Pachyderm does not officially support Microk8s, as Microk8s uses `containerd`. As a workaround, deploy Pachyderm to the cluster with the following flag:

```bash
# configure local kubectl first! pachctl will use its current context
pachctl deploy local --no-expose-docker-socket
```

For better accessibility, you can optionally expose `pachd` as a *LoadBalancer*:

```bash
kubectl patch svc pachd -p '{"spec": {"type": "LoadBalancer"}}'
```

## Issues

- There are issues as Pachyderm not fully supports microk8s, since microk8s uses `containerd` instead of docker (problems with docker.socks), thus the flag upon deployment.
- When deleting pipelines, the k8s resources may remain and need to be deleted manually.
- Undeleted resources may lead to failures when creating new pipelines, in this case you should redeploy Pachyderm.
- The UI sometimes hangs, a browser refresh helps.
- GPU resource requests lead to pipeline crash, possible to lacking support of Microk8s `containerd`.
- In the context of our setup, the Pachyderm service is hard to access locally, as it does not support Socks proxies. We recommend to experiment with Pachyderm using notebooks provided by Determined AI, to stay within the network.

# Determined AI

[https://www.determined.ai/](https://www.determined.ai/)
Version: 0.15.3

Determined AI provides a deep learning platform to train models and a registry to store the trained models. We use a helm chart to deploy Determined AI, thus make sure you have *helm* installed locally on your machine: [https://helm.sh/docs/intro/install/](https://helm.sh/docs/intro/install/).

For complete information about configuring the *helm* chart, you can visit the [installation guidelines](https://docs.determined.ai/latest/how-to/installation/kubernetes.html). We provide a configuration in the setup folder at `setup/detai-setup`. The following instructions deploy Determined AI to our Microk8s cluster:

- For our installation, we used Determined version `0.15.3`, you can also choose to upgrade. The version to be deployed is specified at `setup/detai-setup/Chart.yaml`
- Model checkpoints are to be stored within Minio, as a shared file system rises issues with testing and deployment of models due to accessibility. Thus create a bucket in Minio named `detai` (you can use the web UI at VM). Navigate to the helm chart definition at `setup/detai-setup/values.yaml` and update the manifest:

```bash
checkpointStorage:
..
type: s3
  bucket: detai
  accessKey: minio
  secretKey: miniokey
  endpointUrl: http://172.23.76.93:9000
```

- Now deploy Determined AI to Microk8s using the updated *helm* chart:

```bash
cd setup
# "determined" will be the name of your deployment
# "detai-setup" is the folder where the helm chart is specified
helm install determined detai-setup
```

## Issues

- Currently, Determined AI on Kubernetes only works with GPUs, you cannot use CPUs for training. As only a VM on ScienceCloud has a maximum of 1 GPU, you would have to attach additional VMs to the cluster for distributed training.

# Seldon

[https://www.seldon.io/](https://www.seldon.io/)
Version: 1.17

To deploy deep learning models to our cluster, we use Seldon Core. Seldon allows to simply specify a model wrapper which loads the model and defines the prediction function, then deploys the model wrapper within a Docker container to Kubernetes and exposes the inference service either as a REST API or gRPC service.

To install Seldon on Microk8s, again make sure you have *helm* installed locally. Then follow these instructions:

- Create a namespace for Seldon:

```bash
kubectl create namespace seldon-system
```

- Deploy Seldon using helm:

```bash
helm install seldon-core seldon-core-operator \
    --repo https://storage.googleapis.com/seldon-charts \
    --set usageMetrics.enabled=true \
    --namespace seldon-system \
    --set istio.enabled=true
```

- Create a gateway, you can use the one provided in the `setup` folder:

```bash
kubectl apply -f setup/seldon-setup/gateway.yaml
```

## Issues

- There is currently an issue when serving TensorFlow/Keras models. Refer to the issues here on [GitHub](https://github.com/keras-team/keras/issues/6462) and [Stack Overflow](https://stackoverflow.com/questions/54652536/keras-tensorflow-backend-error-tensor-input-10-specified-in-either-feed-de). You will therefor not receive a successful response when sending prediction requests

# LabelStudio

[https://labelstud.io/](https://labelstud.io/)
Version: 1.0.1

We use LabelStudio to label our data. The Pachyderm Enterprise edition exposes an S3 Gateway for each repository, which allows us to import into and export from LabelStudio. LabelStudio is easy to install with the provided `pip` package, however you can also choose to run it within a [Docker Container](https://hub.docker.com/r/heartexlabs/label-studio). To install and run LabelStudio using python, follow these instructions:

- You can find the official installation instructions [here](https://labelstud.io/guide/install.html).
- We run LabelStudio on the VM that hosts the Microk8s cluster with Pachyderm installed to provide easier access to the repositories.

```bash
sudo apt-get install python3-venv
mkdir lsvenv
python3 -m venv lsvenv

source lsvenv/bin/activate
python -m pip install -U label-studio

# start label-studio
source lsvenv/bin/activate
label-studio
```

## Export and Import Buckets

To ingest data from Pachyderm and export labels to a pachyderm repository, create a project within LabelStudio, then navigate to `Settings > Cloud Storage > Add Source / Target Storage`. 

- Bucket name: `<branch>.<repo>`, e.g. master.fmnist
- S3 Endpoint: `http://<Pachyderm-ClusterIP>:30600`, e.g. `http://10.152.183.24:30600`. You can find this address using `kubectl get all`
- Access ID & Secret: any non-empty string, e.g. `any`
- Enable `Treatevery bucket object as a source file`

## Troubleshooting

- Due to a CORS issue, text data cannot be displayed directly, only the corresponding link, images work fine

# GitLab

[https://about.gitlab.com/de-de/](https://about.gitlab.com/de-de/)

Version: 13.11.3-ee (GitLab Enterprise Edition)

We recommend using a separate VM to install GitLab. If you chose to work with the managed solution, keep in mind that you will not be able to set up the CI/CD pipeline as the cluster is not reachable from the internet, unless you have a public IP.

- To install GitLab on Ubuntu, follow the official instructions: [https://about.gitlab.com/install/#ubuntu](https://about.gitlab.com/install/#ubuntu)
- As external URL, you can use the IP of the VM:

```bash
# at step 2, use the IP of your VM as the address, without https but http
sudo EXTERNAL_URL="http://172.23.80.147" apt-get install gitlab-ee
```

## Integrate GitLab into Microk8s

To later deploy models to the cluster and apply CI/CD, GitLab can inject a [GitLab Runner](https://docs.gitlab.com/runner/) into a Kubernetes cluster. 

- Before you install the integration, you need to allow outbound requests: Within GitLab, navigate to `Admin Area > Settings > Outbound Requests`: *Allow to local network*
- To install the runner, follow the [official instructions](https://ubuntu.com/tutorials/gitlab-cicd-pipelines-with-microk8s#5-gitlab-integration) from Ubuntu.
- Disable `RBAC-enabled cluster`

The following commands will give you the necessary information for the integration:

```bash
# API URL -> clusters/cluster/server
microk8s config

# CA CERTIFICATE
kubectl get secrets
# in this case, the corresponding token is default-token-lqvdd
# copy the token including the -----BEGIN/END CERTIFICATE-----
kubectl get secret default-token-lqvdd  -o jsonpath="{['data']['ca\.crt']}" | base64 --decode

# TOKEN
# navigate to the provided setup folder to create a service account
cd setup/gitlab-setup
kubectl apply -f gitlab-admin-service-account.yaml
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep gitlab | awk '{print $1}')
```

- Finally, navigate to `Admin Area > Kubernetes > Your Cluster > Applications` and install the GitLab Runner.

## Docker Credentials

Navigate to `Admin Aread > Settings > CI/CD > Variables` and set the variables to be used within the GitLab pipelines. The credentials are required to push the images built within a job. Do not mark the variables as `Protected`, such that projects have access to these credentials.

- CI_REGISTRY: [docker.io](http://docker.io) (if you use DockerHub)
- CI_REGISTRY_USER: your DockerHub username
- CI_REGISTRY_PASSWORD: your DockerHub password

# Default Credentials

- GitLab
    - User: root
    - Password: gitlabgit
- Minio
    - User: minio
    - Password: miniokey
- Determined
    - User: determined
    - Password: (none)