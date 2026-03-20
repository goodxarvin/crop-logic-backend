FROM docker.iranserver.com/python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Debian/debian mirrors for apt
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* && \
printf '%s\n' \
'deb https://mirror-linux.runflare.com/debian/ bookworm main contrib non-free non-free-firmware' \
'deb https://mirror-linux.runflare.com/debian/ bookworm-updates main contrib non-free non-free-firmware' \
'deb https://mirror-linux.runflare.com/debian-security/ bookworm-security main contrib non-free non-free-firmware' \
'' \
'deb [trusted=yes] https://mirror2.chabokan.net/debian bookworm main contrib non-free non-free-firmware' \
'deb [trusted=yes] https://mirror2.chabokan.net/debian-security bookworm-security main contrib non-free non-free-firmware' \
'' \
'deb http://mirror.iranserver.com/debian/ bookworm main contrib non-free non-free-firmware' \
'deb-src http://mirror.iranserver.com/debian/ bookworm main contrib non-free non-free-firmware' \
> /etc/apt/sources.list

# System deps for MySQL client (pkg-config required by mysqlclient to find libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Python mirrors
RUN pip config --user set global.index-url https://package-mirror.liara.ir/repository/pypi/simple && \
    pip config --user set global.extra-index-url https://mirror.cdn.ir/repository/pypi/simple && \
    pip config --user set global.extra-index-url https://mirror2.chabokan.net/pypi/simple && \
    pip config --user set global.trusted-host package-mirror.liara.ir && \
    pip config --user set global.trusted-host mirror.cdn.ir && \
    pip config --user set global.trusted-host mirror-pypi.runflare.com

RUN    pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
