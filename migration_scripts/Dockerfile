FROM python:3.7-alpine
WORKDIR /migration_scripts
COPY requirements.txt requirements.txt
ENV PYTHONUNBUFFERED=1
RUN apk add build-base jpeg-dev zlib-dev
RUN pip install --upgrade Pillow
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api.py"]