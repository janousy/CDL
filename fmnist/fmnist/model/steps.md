``` bash
ORG_ID=jabalt
IMAGE_NAME=fmnist-train
IMAGE_VERSION=dev
IMAGE_NAME=$ORG_ID/$IMAGE_NAME
```

### Building docker image. 
```
docker build -t $IMAGE_NAME:$IMAGE_VERSION -f fmnist/model/Dockerfile .
```

### Run locally to test
```
docker run -it -d --rm -p 5000:5000 $IMAGE_NAME:$IMAGE_VERSION

```

### Push docker image

```
docker login
docker push $IMAGE_NAME:$IMAGE_VERSION