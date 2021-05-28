``` bash
ORG_ID=jabalt
IMAGE_NAME=bbc-seldon
IMAGE_VERSION=prod
IMAGE_NAME=$ORG_ID/$IMAGE_NAME
```

### Building docker image. 
```
docker build -t $IMAGE_NAME:$IMAGE_VERSION -f bbc/deploy/Dockerfile .
```

### Run locally to test
```
docker run -it --rm -p 5000:5000 $IMAGE_NAME:$IMAGE_VERSION
```

### Push docker image

```
docker login
docker push $IMAGE_NAME:$IMAGE_VERSION