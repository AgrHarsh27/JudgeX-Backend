FROM gcc:latest

# Create non-root unprivileged sandbox user for isolation
RUN groupadd -r sandboxgroup && useradd -r -g sandboxgroup sandboxuser

WORKDIR /sandbox

# Default command
CMD ["g++", "--version"]
