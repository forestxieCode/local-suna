# Kortix Sandbox Docker Image
# 
# Multi-language development environment with:
# - Python 3.11 + popular packages
# - Node.js 20 + npm/yarn/pnpm
# - Playwright for browser automation
# - Common development tools
#
# Build: docker build -t kortix-sandbox:latest -f backend/core/sandbox/Dockerfile .
# Run: docker run --rm -it kortix-sandbox:latest

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    git \
    curl \
    wget \
    vim \
    nano \
    # Node.js dependencies
    ca-certificates \
    gnupg \
    # Playwright browser dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm and yarn
RUN npm install -g pnpm@latest yarn@latest

# Create workspace directory
WORKDIR /workspace

# Install Python packages
RUN pip install --no-cache-dir \
    # Core packages
    numpy \
    pandas \
    matplotlib \
    seaborn \
    scipy \
    scikit-learn \
    # Web frameworks
    fastapi \
    flask \
    requests \
    httpx \
    # Data processing
    beautifulsoup4 \
    lxml \
    pillow \
    # Async
    aiohttp \
    aiofiles \
    # Utilities
    python-dotenv \
    pydantic \
    # Playwright
    playwright \
    && playwright install chromium --with-deps

# Install common Node.js packages
RUN npm install -g \
    typescript \
    ts-node \
    @types/node \
    axios \
    express \
    dotenv

# Create user for running code (security)
RUN useradd -m -s /bin/bash sandbox && \
    chown -R sandbox:sandbox /workspace

# Switch to sandbox user
USER sandbox

# Set environment
ENV PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    PATH="/home/sandbox/.local/bin:$PATH"

# Default command (kept alive by docker-py)
CMD ["/bin/bash"]
