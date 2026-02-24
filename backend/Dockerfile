FROM python:3.12-slim
WORKDIR /app

# Install Terraform + Git
RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip wget git \
    && wget -q https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip -O /tmp/tf.zip \
    && unzip /tmp/tf.zip -d /usr/local/bin/ \
    && rm /tmp/tf.zip \
    && mkdir -p /app/data \
    && wget -q https://git.io/GeoLite2-Country.mmdb -O /app/data/GeoLite2-Country.mmdb || true \
    && apt-get purge -y unzip wget \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Plugin cache shared across all workspaces
ENV TF_PLUGIN_CACHE_DIR=/tmp/tf-plugin-cache
RUN mkdir -p /tmp/tf-plugin-cache

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
