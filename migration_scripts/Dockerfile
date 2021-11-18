FROM python:3.7-alpine
WORKDIR /migration_scripts
COPY requirements.txt requirements.txt
ENV PYTHONUNBUFFERED=1
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api.py"]