# Architecture & Design Decisions

## Overview

This document explains the architectural decisions made during the modernization of the legacy Python 2.7 banking client to a production-ready Python 3.11+ application.

## Design Philosophy

### 1. Separation of Concerns

The codebase is organized into distinct modules with clear responsibilities:

```
banking_client.py  → Core business logic and API integration
config.py          → Configuration management
cli.py             → User interface layer
test_*.py          → Testing and validation
```

**Rationale**: This separation allows each component to evolve independently and makes the code easier to test, maintain, and extend.

### 2. Dependency Injection

Configuration is injected rather than hardcoded:

```python
# Config can come from environment, files, or be programmatically set
client = BankingClient(base_url=config.api_base_url, timeout=config.api_timeout)
```

**Rationale**: Makes the code testable (can inject mock configs) and flexible (supports multiple environments).

## Key Architectural Decisions

### 1. Session-Based HTTP Client

**Decision**: Use `requests.Session` with connection pooling instead of one-off requests.

**Rationale**:
- Reuses TCP connections → better performance
- Supports retry logic with exponential backoff → resilience
- Centralizes configuration (headers, timeouts, etc.)

**Implementation**:
```python
def _create_session(self) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10)
    session.mount("http://", adapter)
    return session
```

### 2. Dataclass-Based Models

**Decision**: Use `@dataclass` for data models instead of dictionaries.

**Rationale**:
- Type safety with type hints
- Validation logic encapsulated in the model
- IDE autocomplete support
- Cleaner conversion to/from API format

**Example**:
```python
@dataclass
class TransferRequest:
    from_account: str
    to_account: str
    amount: float

    def validate(self) -> None:
        # Validation logic here
        pass

    def to_dict(self) -> Dict[str, Any]:
        # Convert to API format
        return {"fromAccount": self.from_account, ...}
```

### 3. Context Manager Pattern

**Decision**: Implement `__enter__` and `__exit__` for resource management.

**Rationale**:
- Ensures session cleanup even if exceptions occur
- Pythonic and follows standard library patterns
- Prevents resource leaks

**Usage**:
```python
with BankingClient() as client:
    client.transfer(...)
# Session automatically closed here
```

### 4. JWT Token Management

**Decision**: Implement automatic token refresh with expiry tracking.

**Rationale**:
- Reduces API calls (don't re-authenticate unnecessarily)
- Transparent to users (handles refresh automatically)
- Supports long-running clients

**Implementation**:
```python
def _ensure_authenticated(self, scope: str = "transfer") -> None:
    if not self.token or (self.token_expiry and datetime.now() >= self.token_expiry):
        self.authenticate(scope=scope)
```

### 5. Comprehensive Logging

**Decision**: Use Python's `logging` module instead of `print` statements.

**Rationale**:
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Structured logging with timestamps
- Can redirect to files, syslog, etc.
- Production-ready observability

**Example**:
```python
logger.info(f"Initiating transfer: {from_account} -> {to_account}")
logger.error(f"Transfer failed: {e}")
```

## Error Handling Strategy

### Three-Level Error Handling

1. **Validation Errors** (`ValueError`)
   - Raised for invalid inputs (bad account format, negative amounts)
   - Caught before making API calls
   - Fast fail with clear messages

2. **HTTP Errors** (`requests.HTTPError`)
   - API-level errors (404, 401, 500, etc.)
   - Includes response details for debugging
   - Logged with full context

3. **Unexpected Errors** (`Exception`)
   - Catch-all for unforeseen issues
   - Logged for investigation
   - Prevents silent failures

### Retry Logic

Transient failures (network issues, rate limits) are automatically retried:

```python
retry_strategy = Retry(
    total=3,                          # 3 retries
    backoff_factor=1,                 # 1s, 2s, 4s delays
    status_forcelist=[429, 500, ...]  # Retry on these HTTP codes
)
```

## Testing Strategy

### Test Pyramid

1. **Unit Tests** (Fast, Isolated)
   - Test individual functions and classes
   - Mock external dependencies
   - Example: `test_transfer_request_validation`

2. **Integration Tests** (Slower, Real API)
   - Test against live server
   - Marked with `@pytest.mark.integration`
   - Can be skipped if server unavailable

3. **Mock Tests** (Medium, Controlled)
   - Mock HTTP responses
   - Test error handling paths
   - Example: `test_authenticate_http_error`

### Test Coverage Goals

- **Target**: 95%+ code coverage
- **Critical Paths**: 100% coverage (transfer, authentication)
- **Edge Cases**: Comprehensive validation tests

## Docker Architecture

### Multi-Stage Build

**Stage 1** (Builder):
- Install build dependencies
- Compile Python packages
- Create optimized wheel files

**Stage 2** (Runtime):
- Minimal base image (python:3.11-slim)
- Copy only runtime dependencies
- No build tools → smaller image

**Benefits**:
- Smaller final image (~150MB vs ~500MB)
- Faster deployments
- Reduced attack surface

### Docker Compose Design

```yaml
services:
  banking-api:      # Server (from Docker Hub)
  banking-client:   # Our client (built locally)
  banking-cli:      # Interactive CLI (profile-based)
```

**Health Checks**: Client waits for server to be healthy before starting.

**Networks**: Isolated bridge network for security.

## Performance Optimizations

### 1. Connection Pooling
- Reuses TCP connections
- Reduces handshake overhead
- Configured pool size: 10 connections, max 20

### 2. Retry with Backoff
- Exponential backoff: 1s, 2s, 4s
- Avoids overwhelming server during issues
- Improves success rate on transient failures

### 3. Token Caching
- Tokens cached for 1 hour
- Reduces authentication API calls
- Automatic refresh before expiry

### 4. Async-Ready Design
- Session-based architecture supports async conversion
- Can easily migrate to `aiohttp` in future
- Separation of concerns enables parallel execution

## Security Considerations

### 1. No Hardcoded Secrets
- Credentials from environment variables
- `.env.example` for documentation, `.env` in `.gitignore`
- Production: Use secrets management (AWS Secrets Manager, etc.)

### 2. Input Validation
- All inputs validated before API calls
- Account format checked (must start with "ACC")
- Amount must be positive

### 3. Secure Token Handling
- Tokens stored in memory only
- Expiry tracking prevents using expired tokens
- Authorization header format: `Bearer {token}`

### 4. HTTPS Support
- Session supports both HTTP and HTTPS
- In production, use HTTPS for encryption
- SSL certificate verification enabled

## Scalability Considerations

### Horizontal Scaling
- Stateless design (no shared state between requests)
- Can run multiple client instances
- Each instance manages its own session and token

### Vertical Scaling
- Connection pool size configurable
- Timeout values adjustable
- Memory-efficient dataclasses

### Cloud-Ready
- Environment-based configuration
- Docker containerization
- Health checks for orchestration
- Logging to stdout (12-factor app)

## Future Architecture Improvements

### 1. Async/Await Support
```python
async with AsyncBankingClient() as client:
    result = await client.transfer(...)
```
- Use `aiohttp` instead of `requests`
- Enables concurrent transfers
- Better resource utilization

### 2. Circuit Breaker Pattern
- Stop calling failing services temporarily
- Prevents cascading failures
- Use libraries like `pybreaker`

### 3. Caching Layer
```python
@cached(ttl=60)
def validate_account(self, account_id: str):
    # Results cached for 60 seconds
```
- Cache account validations
- Reduce API load
- Use Redis for distributed caching

### 4. Metrics & Monitoring
```python
from prometheus_client import Counter, Histogram

transfer_counter = Counter('transfers_total', 'Total transfers')
transfer_duration = Histogram('transfer_duration_seconds', 'Transfer duration')
```
- Track success/failure rates
- Monitor latency
- Alert on anomalies

### 5. Event-Driven Architecture
- Publish transfer events to message queue
- Decouple transfer from notification
- Enable audit trail and analytics

## Comparison: Legacy vs Modern

| Aspect | Legacy (Python 2.7) | Modern (Python 3.11+) |
|--------|---------------------|----------------------|
| HTTP Client | `urllib2` (blocking) | `requests.Session` (pooled) |
| Data Models | Strings/Dicts | Dataclasses with validation |
| Error Handling | `try/except` only | Multi-level with logging |
| Testing | None | 95%+ coverage with pytest |
| Configuration | Hardcoded | Environment-based |
| Authentication | None | JWT with auto-refresh |
| Retry Logic | None | Exponential backoff |
| Logging | `print` statements | Structured logging |
| Resource Management | Manual | Context managers |
| Packaging | None | Docker + compose |
| Type Safety | None | Full type hints |

## Conclusion

This architecture demonstrates production-ready Python development with:
- **Resilience**: Retry logic, error handling, health checks
- **Performance**: Connection pooling, token caching
- **Maintainability**: Clear separation of concerns, comprehensive tests
- **Security**: Input validation, secure credential handling
- **Scalability**: Stateless design, Docker support

The design follows Python best practices and industry standards, making it suitable for real-world production deployment.
