# Use Alpine Linux for minimal footprint
FROM alpine:3.18

# Install dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-cryptography

# Copy enclave code
COPY enclave.py /enclave.py

# Create non-root user for security
RUN adduser -D nitrouser
USER nitrouser

# Start the VSOCK server on launch
CMD ["python3", "/enclave.py"]