FROM python:3.8-slim

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install 'uvicorn[standard]'
RUN pip install fastapi
RUN pip install fastapi

RUN apt-get update && apt-get install -y net-tools curl iputils-ping && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8014

CMD ["python", "main.py"]
