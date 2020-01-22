FROM python:3.7-alpine
WORKDIR /migration_scripts
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api.py"]