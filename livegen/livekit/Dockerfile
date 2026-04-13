# LiveKit Server - Production Ready
# Use official image with custom configuration

FROM livekit/livekit-server:latest

# Copy custom config
COPY livekit/livekit.yaml /etc/livekit.yaml

# Health check using LiveKit's built-in health endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:7880/health || exit 1

EXPOSE 7880 7881 7882 3478 5349

# Use config file
CMD ["--config", "/etc/livekit.yaml"]
