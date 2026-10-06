FROM python:3.10-alpine

# Create non-root unprivileged sandbox user for isolation
RUN addgroup -S sandboxgroup && adduser -S sandboxuser -G sandboxgroup

WORKDIR /sandbox

# Default command
CMD ["python3"]
