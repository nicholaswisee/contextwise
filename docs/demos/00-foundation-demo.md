# Milestone 0 — Clean Checkout Demo Transcript

Tested on a machine with: git, Python 3.12+, uv 0.12+, Docker + Compose, make.

```bash
# 1. Clone the repository
git clone git@github.com:nicholaswisee/contextwise.git
cd contextwise

# 2. Start the local stack
make up
# Expected: postgres + api containers become healthy

# 3. Check liveness (no external dependency)
python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',8000)); s.send(b'GET /health/live HTTP/1.1\r\nHost: localhost\r\n\r\n'); print(s.recv(4096).decode())"
# Expected: HTTP/1.1 200 OK with {"status": "alive"}

# 4. Check readiness (depends on postgres)
python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',8000)); s.send(b'GET /health/ready HTTP/1.1\r\nHost: localhost\r\n\r\n'); print(s.recv(4096).decode())"
# Expected: HTTP/1.1 200 OK with {"status": "ready"}

# 5. Stop postgres and see readiness fail while liveness stays up
docker compose stop postgres
python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',8000)); s.send(b'GET /health/ready HTTP/1.1\r\nHost: localhost\r\n\r\n'); print(s.recv(4096).decode())"
# Expected: HTTP/1.1 503 Service Unavailable

# 6. Restart postgres and run the same checks CI runs
make down
make up
make check

# 7. Run integration tests (starts a test database)
make test-integration
```

Notes:
- Port 5435 is used on the host for the main postgres container (5432 was occupied).
- Port 5434 is used for the integration-test postgres container.
- No API keys or secrets are required for this milestone.
