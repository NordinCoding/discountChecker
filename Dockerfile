FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0


EXPOSE 80

# For development
CMD ["python", "-u" ,"app.py"]

# When pushing to production/testing production
#CMD ["waitress-serve", "--host=0.0.0.0", "--port=80", "app:app"]