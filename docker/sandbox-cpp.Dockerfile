# docker/sandbox-cpp.Dockerfile
FROM gcc:13.2

RUN useradd -m coder

WORKDIR /workspace

USER coder

CMD ["true"]