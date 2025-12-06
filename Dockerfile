# Use official Python slim image for smaller final image size
FROM python:3.11-slim

# Copy Node.js binaries and libraries from the official image
# This is cleaner and lighter than installing via apt-get
COPY --from=node:22-slim /usr/local/bin /usr/local/bin
COPY --from=node:22-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

# Install uv package manager by copying the binary from the official image
# This is faster and more reliable than installing via pip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Build arguments for private NPM registry authentication
# These values are available only during the build process and not persisted in the final image history
ARG GCP_NPM_TOKEN

# Enable Python bytecode compilation for faster container startup
ENV UV_COMPILE_BYTECODE=1


# --------------------------------------------------------------
# MCP Server Configuration
# --------------------------------------------------------------

# Copy npm configuration
COPY .npmrc .

# Configure authentication for private NPM registry
# Decode the base64 service account key into a temporary file and set credentials path
RUN echo "$GCP_NPM_TOKEN" | base64 -d > /tmp/key.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/tmp/key.json

# Authenticate with Google Artifact Registry using the service account credentials
RUN npx google-artifactregistry-auth

# Install the private MCP server package using package.json
COPY package*.json ./
RUN npm install


# Security: Remove the temporary service account key file
RUN rm /tmp/key.json

# --------------------------------------------------------------


# --------------------------------------------------------------
# Python application setup
# --------------------------------------------------------------

# Copy dependency definition files first
# This allows Docker to cache the dependency installation layer if these files haven't changed
COPY pyproject.toml uv.lock ./

# Install dependencies only (without the project code)
# --frozen: ensures usage of exact versions from uv.lock
# --no-install-project: skips installing the project package itself as source code isn't copied yet
RUN uv sync --frozen --no-install-project

# Copy the rest of the application source code
COPY . .

# Install the project itself into the virtual environment
RUN uv sync --frozen

# Add the virtual environment to the PATH
# This ensures python and uvicorn commands run from the isolated environment (.venv)
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Start the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
