```
ORG_ID=jabalt
IMAGE_NAME=bbc-pach
IMAGE_VERSION=dev
IMAGE_NAME=$ORG_ID/$IMAGE_NAME
DOCKER_FILE_PATH=bbc/data/pipeline/Dockerfile
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