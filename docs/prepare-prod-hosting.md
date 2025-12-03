# Production Hosting Setup Guide

This guide explains how to deploy the UIKit Agent project to a production environment (e.g., Hetzner VPS).

## 1. Domain Configuration (nip.io)

To simplify deployment without purchasing a custom domain immediately, we use [nip.io](https://nip.io/). This service allows us to map a domain to an IP address automatically, enabling automatic SSL certificate generation via Let's Encrypt (handled by Traefik).

-   **Concept**: The domain format is `uikit-agent.<YOUR_SERVER_IP>.nip.io`.
-   **Example**: If your server IP is `192.0.2.1`, your domain will be `uikit-agent.192.0.2.1.nip.io`.

Ensure you update your `.env` file with this domain structure later.

## 2. Private NPM on Google Cloud preparation

Go to **Google Cloud Console -> IAM & Admin -> Service Accounts** and generate a key. It must be a JSON key for authorization.

Generate a base64 string from the JSON key using this command:
```sh
cat path/to/new/key.json | base64 | tr -d '\n' | pbcopy
```

Copy the command output (the base64 string) into the `GCP_NPM_TOKEN` environment variable.


## 3. Server Preparation

Connect to your server via SSH:

```bash
ssh root@<YOUR_SERVER_IP>
```

### System Updates
Update the package list and upgrade existing packages:

```bash
apt update && apt upgrade -y
```

### Install Docker
Install Docker Engine and the Docker Compose plugin:

```bash
apt install -y docker.io docker-compose-v2
```

### Install uv (Python Package Manager)
We use `uv` for fast Python package management:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 4. Security Configuration (UFW)

Set up the firewall to allow necessary traffic (SSH, HTTP, HTTPS):

```bash
ufw allow 22/tcp   # SSH access
ufw allow 80/tcp   # HTTP (Traefik entrypoint)
ufw allow 443/tcp  # HTTPS (Traefik entrypoint)
ufw enable
```

## 5. Project Setup

### Clone Repository
Create a directory for the project and clone the code:

```bash
# Create project directory (using /opt is standard for self-contained apps)
mkdir -p /opt/uikit-agent
cd /opt/uikit-agent

# Clone the repository
git clone https://github.com/6pm/uikit-agent.git .
```

### Configure Environment
Set up the production environment variables:

```bash
# Create .env file from template
cp .env-template .env

# Edit the configuration
nano .env
```
**Important**: Inside `.env`, ensure you update the domain related variables to match the `nip.io` pattern (e.g., `DOMAIN=uikit-agent.<YOUR_IP>.nip.io`).

### Install Local Dependencies (Optional)
If you need to run maintenance scripts or management commands directly on the host machine:

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv sync
```

## 6. Deployment

Build and start the containers using Docker Compose:

```bash
docker compose up -d --build
```

## 7. Verification

Check the status of your containers:

```bash
docker compose ps
```

View application logs to ensure everything started correctly:

```bash
docker compose logs -f
```

You should now be able to access your application at `https://uikit-agent.<YOUR_SERVER_IP>.nip.io` (depending on your Traefik configuration).
