# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **hackathon challenge repository** for the Julius Baer Side Quest - Application Modernization Challenge (SingHacks 2025). The repository contains a pre-built Core Banking API server and a workspace for participants to submit their modernized banking client implementations.

**Challenge Goal**: Participants modernize legacy banking client code (Python 2.7, ES5 JavaScript, or Java 6) to integrate with a REST API using modern language features and best practices.

**Time Limit**: 1.5 hours

## Repository Structure

```
julius-baer-side-quest/
├── server/                       # Pre-built Spring Boot banking API (DO NOT MODIFY)
│   └── core-banking-api.jar     # 26.8 MB executable JAR (Java 17+)
├── submissions/                  # Participant submission workspace
│   ├── my-github-id/            # Example submission folder (template)
│   └── [github-username]/       # Participant folders named by GitHub username
├── README.md                     # Complete challenge instructions (560 lines)
├── SETUP.md                      # Java 17 installation guide
├── Dockerfile                    # Container config for banking API
├── demo_curls_no_jq.sh          # API demo/testing script
└── image.png                     # QR code for repository access
```

## Development Commands

### Running the Banking API Server

The server is **pre-built** and participants **do not modify it**. It provides mock banking services for testing client implementations.

**Using Java (requires Java 17+)**:
```bash
# From repository root
cd server
java -jar core-banking-api.jar

# Run on custom port
java -Dserver.port=8080 -jar core-banking-api.jar
```

**Using Docker**:
```bash
docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest
```

**Verify server is running**:
```bash
curl http://localhost:8123/accounts/validate/ACC1000
# Expected: {"exists": true, "accountId": "ACC1000"}
```

### Testing the API

**Run the demo script**:
```bash
chmod +x demo_curls_no_jq.sh
./demo_curls_no_jq.sh
```

**Access documentation**:
- Swagger UI: http://localhost:8123/swagger-ui.html
- OpenAPI docs: http://localhost:8123/v3/api-docs

### Submission Workflow

Participants work in their own submission folder and submit via Pull Request:

```bash
# Create submission folder
mkdir submissions/your-github-username
cd submissions/your-github-username

# Add your modernized client code, dependencies, and README

# Commit and push (from repo root)
git add submissions/your-github-username/
git commit -m "Add banking client solution by [name]"
git push origin main

# Create PR with title: "Banking Client Solution - [Your Name]"
```

## Architecture

### Server Component (Pre-built, Read-only)

- **Technology**: Spring Boot REST API (Java 17+)
- **Port**: 8123 (default) or configurable via `-Dserver.port`
- **Purpose**: Provides mock banking services with JWT authentication
- **Key Feature**: Scope-based JWT tokens (`enquiry` vs `transfer` scope)

### Client Component (Participant Submissions)

Participants create clients **from scratch** in Java, Python, or JavaScript. The challenge provides legacy code examples that must be modernized:

- **Python 2.7 legacy** → Python 3.x (using `requests`, async/await, type hints)
- **ES5 JavaScript legacy** → ES6+ (using `fetch`, async/await, modules)
- **Java 6 legacy** → Java 11+ (using HttpClient API, var, streams)

### API Endpoints

**Core Endpoints** (required for challenge):
| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| `POST` | `/authToken?claim=enquiry\|transfer` | Get JWT token with scope | No |
| `POST` | `/transfer` | Transfer funds between accounts | No (bonus if yes) |
| `GET` | `/accounts` | List all accounts | No |
| `GET` | `/accounts/validate/{id}` | Validate account exists | No |
| `GET` | `/accounts/balance/{id}` | Get account balance | No |

**Bonus Endpoints**:
| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| `POST` | `/auth/validate` | Validate JWT token | Yes |
| `GET` | `/transactions/history` | Get transaction history | Yes |

### Account Data Ranges

The API uses specific account ID ranges for testing:
- **Valid accounts**: `ACC1000-ACC1099` (can send/receive funds)
- **Invalid accounts**: `ACC2000-ACC2049` (transfers fail validation)
- **Non-existent**: All other IDs (transfers fail)

### Transfer Request Format

```json
{
  "fromAccount": "ACC1000",
  "toAccount": "ACC1001",
  "amount": 100.00
}
```

**Success Response**:
```json
{
  "transactionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "message": "Transfer completed successfully",
  "fromAccount": "ACC1000",
  "toAccount": "ACC1001",
  "amount": 100.00
}
```

## Scoring System

| Category | Points | Description |
|----------|--------|-------------|
| Core Modernization | 40 pts | Successfully modernized legacy code to work with API |
| Code Quality | 20 pts | Clean, modern, well-organized code |
| Language Modernization | +10 pts | Proper upgrade to current language standards |
| HTTP Client Modernization | +10 pts | Modern HTTP libraries and patterns |
| Error Handling & Logging | +10 pts | Professional error management |
| Architecture & Design | +15 pts | Modern design patterns, SOLID principles |
| Testing & Documentation | +10 pts | Unit tests, README, migration notes |
| Innovation | +5 pts | Creative modernization solutions |

**Total Possible**: 120 points (60 base + 60 bonus)

## Important Notes for Development

### Participant Code Location

All participant code **must** be in a folder named after their GitHub username inside `submissions/`:
- ✅ Correct: `submissions/john-doe/banking_client.py`
- ❌ Wrong: `submissions/solution/banking_client.py`
- ❌ Wrong: `banking_client.py` (root level)

### What NOT to Modify

- **DO NOT** modify the `server/` directory or `core-banking-api.jar`
- **DO NOT** modify the root-level documentation files (README.md, SETUP.md)
- **DO NOT** modify other participants' submission folders

### Legacy Code Examples

The README.md (lines 213-360) contains three complete legacy code examples that demonstrate anti-patterns:
- Manual JSON string concatenation
- Synchronous/blocking HTTP requests
- Poor error handling (print statements instead of logging)
- Old-style HTTP libraries (urllib2, XMLHttpRequest, HttpURLConnection)
- No input validation or authentication

Participants should modernize these patterns as part of the challenge.

### Authentication Details

JWT tokens have **scope-based permissions**:
- `enquiry` scope: Read-only operations (validate, balance, list)
- `transfer` scope: Full permissions (includes transfer operations)

Get token with scope:
```bash
curl -X POST "http://localhost:8123/authToken?claim=transfer" \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"any"}'
```

Use token in requests:
```bash
curl -X POST "http://localhost:8123/transfer" \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"fromAccount":"ACC1000","toAccount":"ACC1001","amount":50.00}'
```

### Time Management Strategy

Recommended breakdown for the 1.5-hour time limit:
- **20 min**: Setup, explore API, plan approach
- **50 min**: Implement core transfer functionality
- **20 min**: Add one bonus feature (JWT auth or validation)
- **10 min**: Documentation and cleanup

### Git Workflow

This repository is designed for **fork and PR workflow**:
1. Participants fork `https://github.com/SingHacks-2025/julius-baer-side-quest`
2. Create submission folder with their GitHub username
3. Develop their solution
4. Submit via Pull Request to the main repository
5. Solutions become visible to others after submission

## Troubleshooting

### Server Issues

**"Port 8123 already in use"**:
```bash
# Find and kill process on macOS/Linux
lsof -ti:8123 | xargs kill -9

# Or run on different port
java -Dserver.port=8081 -jar server/core-banking-api.jar
```

**"java: command not found"**:
- Ensure Java 17+ is installed (see SETUP.md)
- Verify: `java -version` shows version 17 or higher

### API Testing Issues

**Transfer fails with invalid accounts**:
- Use accounts in range `ACC1000-ACC1099`
- Avoid `ACC2000-ACC2049` (deliberately invalid for testing)

**Authentication fails**:
- Ensure JWT token has correct scope (`transfer` for transfers)
- Check token is not expired
- Verify `Authorization: Bearer TOKEN` header format

## Reference Materials

- **Complete challenge instructions**: README.md
- **Java setup guide**: SETUP.md
- **API demo script**: demo_curls_no_jq.sh
- **Docker setup**: Dockerfile
- **Submission template**: submissions/my-github-id/ (example folder)
