# docker/sandbox-cpp.Dockerfile
FROM gcc:13.2

# Create a non-root user 'coder'
RUN useradd -m coder

WORKDIR /workspace

USER coder

CMD ["true"]