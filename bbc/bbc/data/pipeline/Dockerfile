# the same docker image is used for all pipelines
FROM python:3.7-slim
RUN pip install --no-cache-dir --upgrade pip && \
    pip install psycopg2-binary~=2.7.7
ADD bbc/data/pipeline/validate/validate.py /validate.py
ADD bbc/data/pipeline/label/write_db.py /write_db.py