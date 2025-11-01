"""
Unit tests for Banking Client.
Demonstrates modern Python testing with pytest.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests

from banking_client import (
    BankingClient,
    TransferRequest,
    TransferResponse
)


class TestTransferRequest:
    """Test cases for TransferRequest data model."""

    def test_transfer_request_creation(self):
        """Test creating a transfer request."""
        req = TransferRequest(
            from_account="ACC1000",
            to_account="ACC1001",
            amount=100.0
        )

        assert req.from_account == "ACC1000"
        assert req.to_account == "ACC1001"
        assert req.amount == 100.0

    def test_transfer_request_to_dict(self):
        """Test converting transfer request to dictionary."""
        req = TransferRequest("ACC1000", "ACC1001", 100.0)
        data = req.to_dict()

        assert data["fromAccount"] == "ACC1000"
        assert data["toAccount"] == "ACC1001"
        assert data["amount"] == 100.0

    def test_validate_valid_request(self):
        """Test validation of valid transfer request."""
        req = TransferRequest("ACC1000", "ACC1001", 100.0)
        # Should not raise exception
        req.validate()

    def test_validate_missing_accounts(self):
        """Test validation fails for missing accounts."""
        req = TransferRequest("", "ACC1001", 100.0)
        with pytest.raises(ValueError, match="Both from_account and to_account are required"):
            req.validate()

    def test_validate_invalid_account_format(self):
        """Test validation fails for invalid account format."""
        req = TransferRequest("INVALID", "ACC1001", 100.0)
        with pytest.raises(ValueError, match="Invalid from_account format"):
            req.validate()

    def test_validate_negative_amount(self):
        """Test validation fails for negative amount."""
        req = TransferRequest("ACC1000", "ACC1001", -100.0)
        with pytest.raises(ValueError, match="Amount must be positive"):
            req.validate()

    def test_validate_zero_amount(self):
        """Test validation fails for zero amount."""
        req = TransferRequest("ACC1000", "ACC1001", 0.0)
        with pytest.raises(ValueError, match="Amount must be positive"):
            req.validate()


class TestTransferResponse:
    """Test cases for TransferResponse data model."""

    def test_transfer_response_creation(self):
        """Test creating a transfer response."""
        resp = TransferResponse(
            transaction_id="tx123",
            status="SUCCESS",
            message="Transfer completed",
            from_account="ACC1000",
            to_account="ACC1001",
            amount=100.0
        )

        assert resp.transaction_id == "tx123"
        assert resp.status == "SUCCESS"
        assert resp.amount == 100.0

    def test_from_dict(self):
        """Test creating TransferResponse from dictionary."""
        data = {
            "transactionId": "tx123",
            "status": "SUCCESS",
            "message": "Transfer completed",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.0,
            "timestamp": "2024-01-01T12:00:00"
        }

        resp = TransferResponse.from_dict(data)

        assert resp.transaction_id == "tx123"
        assert resp.status == "SUCCESS"
        assert resp.from_account == "ACC1000"
        assert resp.to_account == "ACC1001"
        assert resp.amount == 100.0
        assert resp.timestamp == "2024-01-01T12:00:00"

    def test_from_dict_missing_fields(self):
        """Test from_dict handles missing fields gracefully."""
        data = {}
        resp = TransferResponse.from_dict(data)

        assert resp.transaction_id == ""
        assert resp.status == "UNKNOWN"
        assert resp.amount == 0.0


class TestBankingClient:
    """Test cases for BankingClient."""

    @pytest.fixture
    def client(self):
        """Create a BankingClient instance for testing."""
        return BankingClient(base_url="http://localhost:8123", timeout=5)

    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        return MagicMock()

    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.base_url == "http://localhost:8123"
        assert client.timeout == 5
        assert client.token is None
        assert client.token_expiry is None

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URL."""
        client = BankingClient(base_url="http://localhost:8123/")
        assert client.base_url == "http://localhost:8123"

    @patch('banking_client.requests.Session')
    def test_authenticate_success(self, mock_session_class, client):
        """Test successful authentication."""
        mock_response = Mock()
        mock_response.json.return_value = {"token": "test_token_123"}
        mock_response.raise_for_status = Mock()

        client.session.post = Mock(return_value=mock_response)

        token = client.authenticate(username="alice", password="secret", scope="transfer")

        assert token == "test_token_123"
        assert client.token == "test_token_123"
        assert client.token_expiry is not None

        # Verify the call
        client.session.post.assert_called_once()
        call_args = client.session.post.call_args
        assert "authToken" in call_args[0][0]
        assert call_args[1]["params"] == {"claim": "transfer"}

    @patch('banking_client.requests.Session')
    def test_authenticate_http_error(self, mock_session_class, client):
        """Test authentication with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")

        client.session.post = Mock(return_value=mock_response)

        with pytest.raises(requests.HTTPError):
            client.authenticate(username="invalid", password="invalid")

    def test_get_headers_no_auth(self, client):
        """Test getting headers without authentication."""
        headers = client._get_headers(use_auth=False)

        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    def test_get_headers_with_auth(self, client):
        """Test getting headers with authentication."""
        client.token = "test_token_123"
        headers = client._get_headers(use_auth=True)

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test_token_123"

    @patch('banking_client.requests.Session')
    def test_transfer_success(self, mock_session_class, client):
        """Test successful transfer."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "transactionId": "tx123",
            "status": "SUCCESS",
            "message": "Transfer completed",
            "fromAccount": "ACC1000",
            "toAccount": "ACC1001",
            "amount": 100.0
        }
        mock_response.raise_for_status = Mock()

        client.session.post = Mock(return_value=mock_response)

        result = client.transfer("ACC1000", "ACC1001", 100.0, use_auth=False)

        assert result.transaction_id == "tx123"
        assert result.status == "SUCCESS"
        assert result.amount == 100.0

    def test_transfer_invalid_amount(self, client):
        """Test transfer with invalid amount."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            client.transfer("ACC1000", "ACC1001", -100.0)

    def test_transfer_invalid_account_format(self, client):
        """Test transfer with invalid account format."""
        with pytest.raises(ValueError, match="Invalid from_account format"):
            client.transfer("INVALID", "ACC1001", 100.0)

    @patch('banking_client.requests.Session')
    def test_validate_account_success(self, mock_session_class, client):
        """Test successful account validation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "accountId": "ACC1000",
            "isValid": True,
            "accountType": "VALID_ACCOUNT",
            "status": "ACTIVE"
        }
        mock_response.raise_for_status = Mock()

        client.session.get = Mock(return_value=mock_response)

        result = client.validate_account("ACC1000")

        assert result["accountId"] == "ACC1000"
        assert result["isValid"] is True

    @patch('banking_client.requests.Session')
    def test_get_balance_success(self, mock_session_class, client):
        """Test successful get balance."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "accountId": "ACC1000",
            "balance": 1000.0,
            "currency": "USD"
        }
        mock_response.raise_for_status = Mock()

        client.session.get = Mock(return_value=mock_response)

        result = client.get_balance("ACC1000")

        assert result["accountId"] == "ACC1000"
        assert result["balance"] == 1000.0

    @patch('banking_client.requests.Session')
    def test_list_accounts_success(self, mock_session_class, client):
        """Test successful list accounts."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "accounts": [
                {"accountId": "ACC1000", "status": "ACTIVE"},
                {"accountId": "ACC1001", "status": "ACTIVE"}
            ]
        }
        mock_response.raise_for_status = Mock()

        client.session.get = Mock(return_value=mock_response)

        result = client.list_accounts()

        assert len(result["accounts"]) == 2

    def test_ensure_authenticated_with_valid_token(self, client):
        """Test ensure_authenticated with valid token."""
        client.token = "valid_token"
        client.token_expiry = datetime.now() + timedelta(hours=1)

        # Should not raise or re-authenticate
        client._ensure_authenticated()

        assert client.token == "valid_token"

    @patch.object(BankingClient, 'authenticate')
    def test_ensure_authenticated_with_expired_token(self, mock_auth, client):
        """Test ensure_authenticated with expired token."""
        client.token = "expired_token"
        client.token_expiry = datetime.now() - timedelta(hours=1)

        mock_auth.return_value = "new_token"

        client._ensure_authenticated()

        mock_auth.assert_called_once()

    def test_context_manager(self):
        """Test client as context manager."""
        with BankingClient() as client:
            assert client.session is not None

        # Session should be closed after exiting context

    def test_close(self, client):
        """Test closing the client."""
        mock_session = Mock()
        client.session = mock_session

        client.close()

        mock_session.close.assert_called_once()


class TestIntegration:
    """Integration tests (require running server)."""

    @pytest.fixture
    def live_client(self):
        """Create a client connected to live server."""
        return BankingClient(base_url="http://localhost:8123")

    @pytest.mark.integration
    def test_validate_account_integration(self, live_client):
        """Integration test for account validation."""
        result = live_client.validate_account("ACC1000")
        assert result["isValid"] is True

    @pytest.mark.integration
    def test_transfer_integration(self, live_client):
        """Integration test for transfer."""
        result = live_client.transfer("ACC1000", "ACC1001", 10.0, use_auth=False)
        assert result.status == "SUCCESS"
        assert result.amount == 10.0


# Run tests with: pytest test_banking_client.py -v
# Run with coverage: pytest test_banking_client.py -v --cov=banking_client --cov-report=html
# Skip integration tests: pytest test_banking_client.py -v -m "not integration"
