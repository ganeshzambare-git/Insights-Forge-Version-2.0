# Authentication Architecture — Insight Forge V2

This document details the stateless JWT authentication system.

---

## 1. Cryptographic Handshake

- **Algorithm**: `HS256` (Symmetric HMAC-SHA256 algorithm utilizing a 32+ character secret key).
- **Key Storage**: Keys are read dynamically on startup from the `JWT_SECRET` (or `SECRET_KEY` / `JWT_SECRET_KEY`) environment variables.

---

## 2. JWT Claims Specification

Every generated token contains the following claims payload:

```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "role": "Faculty",
  "jti": "session-token-jti",
  "type": "access",
  "iss": "insight-forge-v2",
  "aud": "insight-forge-v2-client",
  "iat": 1782347234,
  "nbf": 1782347234,
  "exp": 1782348234
}
```

- `sub`: Subject identifier mapping to the unique user UUID.
- `tenant_id`: Mandatory tenant identification claim to ensure strict data partitioning.
- `role`: Encodes the user's role (`Admin`, `Dean`, `Faculty`, `Student`) for quick access checks.
- `jti`: JSON Web Token ID claim matched against the database `sessions` table.
- `type`: Classified as `"access"` or `"refresh"`.
- `iss`/`aud`: Standard issuer and audience validation.

---

## 3. Session Lifecycle, Rotation & Reuse Detection

1. **Session Persistence**: Sessions are tracked in the database by `jwt_jti`. No raw token strings are stored.
2. **Access Token Lifetime**: 15 minutes.
3. **Refresh Token Lifetime**: 7 days (extended to 30 days if `remember_me=True` is provided on login).
4. **Token Rotation**: Refreshing generates a new access token, deletes the old database session JTI, generates a new JTI, creates a new session in the database, and returns the new token pair.
5. **Replay/Reuse Detection**: If a revoked or rotated JTI is reused (i.e. it is decoded from a refresh request but missing in active DB sessions), it is logged as a `TOKEN_REUSE_DETECTED` security alert and rejected instantly.

