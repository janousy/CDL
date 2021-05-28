FROM python:3.7-slim
COPY fmnist/deploy/FashionModel.py /app/
COPY fmnist/deploy/requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000

# Define environment variable
ENV MODEL_NAME FashionModel
ENV SERVICE_TYPE MODEL
ENV PERSISTENCE 0

CMD exec seldon-core-microservice $MODEL_NAME --service-type $SERVICE_TYPE --persistence $PERSISTENCE