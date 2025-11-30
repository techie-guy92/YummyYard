FROM python:3.12-slim

LABEL maintainer="soheil.dalirii@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1          

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    procps \
    bash \
    iproute2 \
    net-tools \
    lsof \
    postgresql-client \
    build-essential \
    python3-dev \
    openssh-server \
    sudo \
    supervisor \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Configure locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Configure SSH
RUN mkdir -p /var/run/sshd && \
    echo 'PermitRootLogin no' >> /etc/ssh/sshd_config && \
    echo 'PasswordAuthentication no' >> /etc/ssh/sshd_config && \
    echo 'ChallengeResponseAuthentication no' >> /etc/ssh/sshd_config

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN adduser --uid 1000 --disabled-password --gecos '' webuser && \
    mkdir -p /app/logs /app/aws && \
    chown -R webuser:webuser /app && \
    chmod -R 755 /app/aws

COPY ansible_id_ed25519.pub /home/webuser/.ssh/authorized_keys
RUN chown -R webuser:webuser /home/webuser/.ssh && \
    chmod 700 /home/webuser/.ssh && \
    chmod 600 /home/webuser/.ssh/authorized_keys

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000 22

CMD ["/usr/bin/supervisord", "-n"]