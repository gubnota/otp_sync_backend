# [Mobile part see here](https://github.com/gubnota/otp_sync)

## Self-signed certificate

![video](https://github.com/user-attachments/assets/b106ab6e-db6a-45d1-a1f2-f367561ad184)

First you need to generate a self-signed certificate.
Certificate authority is not required to place on the client side.

```bash
openssl genrsa -out private.key 2048
openssl req -new -key private.key -out cert.csr
openssl x509 -req -days 36500 -in cert.csr -signkey private.key -out cert.crt
```

## .env

1. create `.env` (see env.example)
2. make sure BOT_TOKEN is the correct secret for your Telegram bot.

## Run and test

```sh
docker compose up --build
curl -X GET https://localhost:9374/ \
     --cert cert.crt \
     --key private.key \
     --insecure

```

## Running locally without docker

- Using pip:

```bash
pip install -r requirements.txt
```

- Using poetry:

```bash
poetry install
```

- Using uv:

```bash
uv sync
```
