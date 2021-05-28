FROM python:3.7-slim
COPY bbc/deploy/NewsModel.py /app/
COPY bbc/deploy/requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000

# Define environment variable
ENV MODEL_NAME NewsModel
ENV SERVICE_TYPE MODEL
ENV PERSISTENCE 0

CMD exec seldon-core-microservice $MODEL_NAME --service-type $SERVICE_TYPE --persistence $PERSISTENCE