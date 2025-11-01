"""
Modern Banking Client - Python 3.11+
Modernized from legacy Python 2.7 code with best practices.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TransferRequest:
    """Data model for transfer requests."""
    from_account: str
    to_account: str
    amount: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request format."""
        return {
            "fromAccount": self.from_account,
            "toAccount": self.to_account,
            "amount": self.amount
        }

    def validate(self) -> None:
        """Validate transfer request data."""
        if not self.from_account or not self.to_account:
            raise ValueError("Both from_account and to_account are required")

        if not self.from_account.startswith("ACC"):
            raise ValueError(f"Invalid from_account format: {self.from_account}")

        if not self.to_account.startswith("ACC"):
            raise ValueError(f"Invalid to_account format: {self.to_account}")

        if self.amount <= 0:
            raise ValueError(f"Amount must be positive, got: {self.amount}")


@dataclass
class TransferResponse:
    """Data model for transfer responses."""
    transaction_id: str
    status: str
    message: str
    from_account: str
    to_account: str
    amount: float
    timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransferResponse':
        """Create TransferResponse from API response."""
        return cls(
            transaction_id=data.get('transactionId', ''),
            status=data.get('status', 'UNKNOWN'),
            message=data.get('message', ''),
            from_account=data.get('fromAccount', ''),
            to_account=data.get('toAccount', ''),
            amount=data.get('amount', 0.0),
            timestamp=data.get('timestamp')
        )


class BankingClient:
    """
    Modern Banking API Client with JWT authentication and retry logic.

    Features:
    - JWT token management with automatic refresh
    - Connection pooling and retry logic with exponential backoff
    - Comprehensive error handling and logging
    - Type hints and modern Python 3.x syntax
    """

    def __init__(self, base_url: str = "http://localhost:8123", timeout: int = 10):
        """
        Initialize the Banking Client.

        Args:
            base_url: Base URL of the banking API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

        # Setup session with connection pooling and retry logic
        self.session = self._create_session()

        logger.info(f"BankingClient initialized with base_url: {self.base_url}")

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry logic and connection pooling.

        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def authenticate(self, username: str = "alice", password: str = "secret",
                    scope: str = "transfer") -> str:
        """
        Authenticate and get JWT token with specified scope.

        Args:
            username: Username for authentication
            password: Password for authentication
            scope: Token scope ('enquiry' or 'transfer')

        Returns:
            JWT token string

        Raises:
            requests.HTTPError: If authentication fails
        """
        url = f"{self.base_url}/authToken"
        params = {"claim": scope}
        payload = {"username": username, "password": password}

        logger.info(f"Authenticating user '{username}' with scope '{scope}'")

        try:
            response = self.session.post(
                url,
                json=payload,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            self.token = data.get('token')

            # Set token expiry (assuming 1 hour validity)
            self.token_expiry = datetime.now() + timedelta(hours=1)

            logger.info("Authentication successful")
            return self.token

        except requests.HTTPError as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise

    def _ensure_authenticated(self, scope: str = "transfer") -> None:
        """
        Ensure valid JWT token exists, refresh if needed.

        Args:
            scope: Required token scope
        """
        if not self.token or (self.token_expiry and datetime.now() >= self.token_expiry):
            logger.info("Token expired or missing, re-authenticating")
            self.authenticate(scope=scope)

    def _get_headers(self, use_auth: bool = False) -> Dict[str, str]:
        """
        Get request headers, optionally with authentication.

        Args:
            use_auth: Whether to include Authorization header

        Returns:
            Dictionary of headers
        """
        headers = {"Content-Type": "application/json"}

        if use_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    def transfer(self, from_account: str, to_account: str, amount: float,
                use_auth: bool = True) -> TransferResponse:
        """
        Transfer funds between accounts.

        Args:
            from_account: Source account ID (e.g., 'ACC1000')
            to_account: Destination account ID (e.g., 'ACC1001')
            amount: Transfer amount (must be positive)
            use_auth: Whether to use JWT authentication

        Returns:
            TransferResponse object with transaction details

        Raises:
            ValueError: If input validation fails
            requests.HTTPError: If API request fails
        """
        # Create and validate transfer request
        transfer_req = TransferRequest(from_account, to_account, amount)
        transfer_req.validate()

        # Ensure authentication if required
        if use_auth:
            self._ensure_authenticated(scope="transfer")

        url = f"{self.base_url}/transfer"

        logger.info(f"Initiating transfer: {from_account} -> {to_account}, amount: {amount}")

        try:
            response = self.session.post(
                url,
                json=transfer_req.to_dict(),
                headers=self._get_headers(use_auth=use_auth),
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            transfer_resp = TransferResponse.from_dict(data)

            logger.info(f"Transfer successful: {transfer_resp.transaction_id}")
            return transfer_resp

        except requests.HTTPError as e:
            logger.error(f"Transfer failed with HTTP error: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during transfer: {e}")
            raise

    def validate_account(self, account_id: str) -> Dict[str, Any]:
        """
        Validate if an account exists and is active.

        Args:
            account_id: Account ID to validate

        Returns:
            Account validation response
        """
        url = f"{self.base_url}/accounts/validate/{account_id}"

        logger.info(f"Validating account: {account_id}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Account {account_id} validation result: {data.get('isValid')}")
            return data

        except requests.HTTPError as e:
            logger.error(f"Account validation failed: {e}")
            raise

    def get_balance(self, account_id: str, use_auth: bool = False) -> Dict[str, Any]:
        """
        Get account balance.

        Args:
            account_id: Account ID
            use_auth: Whether to use JWT authentication

        Returns:
            Balance information
        """
        if use_auth:
            self._ensure_authenticated(scope="enquiry")

        url = f"{self.base_url}/accounts/balance/{account_id}"

        logger.info(f"Getting balance for account: {account_id}")

        try:
            response = self.session.get(
                url,
                headers=self._get_headers(use_auth=use_auth),
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Balance for {account_id}: {data.get('balance')}")
            return data

        except requests.HTTPError as e:
            logger.error(f"Get balance failed: {e}")
            raise

    def list_accounts(self, use_auth: bool = False) -> Dict[str, Any]:
        """
        List all accounts.

        Args:
            use_auth: Whether to use JWT authentication

        Returns:
            List of accounts
        """
        if use_auth:
            self._ensure_authenticated(scope="enquiry")

        url = f"{self.base_url}/accounts"

        logger.info("Listing all accounts")

        try:
            response = self.session.get(
                url,
                headers=self._get_headers(use_auth=use_auth),
                timeout=self.timeout
            )
            response.raise_for_status()

            return response.json()

        except requests.HTTPError as e:
            logger.error(f"List accounts failed: {e}")
            raise

    def get_transaction_history(self) -> Dict[str, Any]:
        """
        Get transaction history (requires authentication).

        Returns:
            Transaction history
        """
        self._ensure_authenticated(scope="transfer")

        url = f"{self.base_url}/transactions/history"

        logger.info("Getting transaction history")

        try:
            response = self.session.get(
                url,
                headers=self._get_headers(use_auth=True),
                timeout=self.timeout
            )
            response.raise_for_status()

            return response.json()

        except requests.HTTPError as e:
            logger.error(f"Get transaction history failed: {e}")
            raise

    def close(self) -> None:
        """Close the session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.info("BankingClient session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Example usage of the Banking Client."""
    # Using context manager for automatic cleanup
    with BankingClient() as client:
        try:
            # Example 1: Transfer with authentication
            print("\n=== Example 1: Transfer with JWT Authentication ===")
            client.authenticate(username="alice", password="secret", scope="transfer")

            result = client.transfer(
                from_account="ACC1000",
                to_account="ACC1001",
                amount=100.00,
                use_auth=True
            )

            print(f"✅ Transfer successful!")
            print(f"   Transaction ID: {result.transaction_id}")
            print(f"   Status: {result.status}")
            print(f"   Message: {result.message}")
            print(f"   Amount: ${result.amount}")

            # Example 2: Transfer without authentication
            print("\n=== Example 2: Transfer without Authentication ===")
            result2 = client.transfer(
                from_account="ACC1002",
                to_account="ACC1003",
                amount=50.00,
                use_auth=False
            )
            print(f"✅ Transfer successful! Transaction ID: {result2.transaction_id}")

            # Example 3: Validate accounts
            print("\n=== Example 3: Account Validation ===")
            validation = client.validate_account("ACC1000")
            print(f"Account ACC1000 valid: {validation.get('isValid')}")

            validation_invalid = client.validate_account("ACC2000")
            print(f"Account ACC2000 valid: {validation_invalid.get('isValid')}")

            # Example 4: Get balance
            print("\n=== Example 4: Get Account Balance ===")
            balance = client.get_balance("ACC1000")
            print(f"Account ACC1000 balance: ${balance.get('balance')}")

            # Example 5: List accounts
            print("\n=== Example 5: List All Accounts ===")
            accounts = client.list_accounts()
            print(f"Total accounts: {len(accounts.get('accounts', []))}")

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            print(f"❌ Error: {e}")
        except requests.HTTPError as e:
            logger.error(f"API error: {e}")
            print(f"❌ API Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
