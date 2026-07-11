# TODO - Fix connectivity reconnection exhaustion

- [x] Update ConnectivityProvider to remove hardcoded `http://localhost:8000/health` and use configurable/same-origin health URL.

- [x] Add guard to prevent overlapping reconnect sequences / timers.
- [x] Ensure heartbeat interval and reconnect timers are cleared/restarted deterministically.

- [x] Adjust lock behavior so UI isn’t permanently blocked after max attempts.

- [x] Update ConnectionOverlay messaging to reflect health/API rather than “gateway cores”.

- [x] Run frontend build/typecheck and (if available) backend health verification.


