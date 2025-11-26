# docker/sandbox-python.Dockerfile
FROM python:3.12-slim

# Create a non-root user 'coder'
RUN useradd -m coder

# Set working directory
WORKDIR /workspace

# Switch to non-root user for security
USER coder

# Simple command that exits immediately. 
# We only need this image to exist; we don't run it as a service.
CMD ["true"]