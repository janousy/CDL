``` bash
ORG_ID=jabalt
IMAGE_NAME=fmnist-pach
IMAGE_VERSION=1.0
IMAGE_NAME=$ORG_ID/$IMAGE_NAME
DOCKER_FILE_PATH=fmnist/data/Dockerfile
```

### Building docker image. 
```
docker build -t $IMAGE_NAME:$IMAGE_VERSION -f $DOCKER_FILE_PATH .
```

### Run locally to test
```
docker run -it --rm $IMAGE_NAME:$IMAGE_VERSION
```

### Push docker image

```
docker login
docker push $IMAGE_NAME:$IMAGE_VERSION