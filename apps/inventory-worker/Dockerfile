FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY logjson.py inventory.py worker.py ./
USER 10001:10001
EXPOSE 8000
CMD ["python", "worker.py"]
