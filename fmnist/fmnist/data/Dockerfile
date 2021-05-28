FROM python:3.7-slim
ADD data/pipeline/validate/validate.py /validate.py
ADD data/pipeline/validate/requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

