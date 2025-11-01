#!/usr/bin/env python3
"""
Modern CLI Interface for Banking Client.
Provides interactive command-line access to banking operations.
"""

import argparse
import sys
from typing import Optional
import json

from banking_client import BankingClient
from config import BankingConfig


def setup_parser() -> argparse.ArgumentParser:
    """
    Setup argument parser for CLI.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Modern Banking Client CLI - Gold Level Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transfer with authentication
  python cli.py transfer --from ACC1000 --to ACC1001 --amount 100 --auth

  # Transfer without authentication
  python cli.py transfer --from ACC1002 --to ACC1003 --amount 50

  # Validate account
  python cli.py validate --account ACC1000

  # Get balance
  python cli.py balance --account ACC1000

  # List all accounts
  python cli.py list-accounts

  # Get transaction history
  python cli.py history
        """
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8123",
        help="Banking API base URL (default: http://localhost:8123)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Transfer command
    transfer_parser = subparsers.add_parser("transfer", help="Transfer funds between accounts")
    transfer_parser.add_argument("--from", dest="from_account", required=True,
                                 help="Source account ID (e.g., ACC1000)")
    transfer_parser.add_argument("--to", dest="to_account", required=True,
                                 help="Destination account ID (e.g., ACC1001)")
    transfer_parser.add_argument("--amount", type=float, required=True,
                                 help="Transfer amount")
    transfer_parser.add_argument("--auth", action="store_true",
                                 help="Use JWT authentication")
    transfer_parser.add_argument("--username", default="alice",
                                 help="Username for authentication (default: alice)")
    transfer_parser.add_argument("--password", default="secret",
                                 help="Password for authentication (default: secret)")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate account")
    validate_parser.add_argument("--account", required=True,
                                help="Account ID to validate")

    # Balance command
    balance_parser = subparsers.add_parser("balance", help="Get account balance")
    balance_parser.add_argument("--account", required=True,
                               help="Account ID")
    balance_parser.add_argument("--auth", action="store_true",
                               help="Use JWT authentication")

    # List accounts command
    list_parser = subparsers.add_parser("list-accounts", help="List all accounts")
    list_parser.add_argument("--auth", action="store_true",
                            help="Use JWT authentication")

    # History command
    history_parser = subparsers.add_parser("history", help="Get transaction history")
    history_parser.add_argument("--username", default="alice",
                               help="Username for authentication (default: alice)")
    history_parser.add_argument("--password", default="secret",
                               help="Password for authentication (default: secret)")

    # Authenticate command
    auth_parser = subparsers.add_parser("auth", help="Get authentication token")
    auth_parser.add_argument("--username", default="alice",
                            help="Username (default: alice)")
    auth_parser.add_argument("--password", default="secret",
                            help="Password (default: secret)")
    auth_parser.add_argument("--scope", choices=["enquiry", "transfer"], default="transfer",
                            help="Token scope (default: transfer)")

    return parser


def handle_transfer(client: BankingClient, args: argparse.Namespace) -> int:
    """Handle transfer command."""
    try:
        if args.auth:
            print(f"🔐 Authenticating as {args.username}...")
            client.authenticate(username=args.username, password=args.password, scope="transfer")

        print(f"\n💸 Transferring ${args.amount:.2f} from {args.from_account} to {args.to_account}...")

        result = client.transfer(
            from_account=args.from_account,
            to_account=args.to_account,
            amount=args.amount,
            use_auth=args.auth
        )

        print("\n✅ Transfer Successful!")
        print(f"   Transaction ID: {result.transaction_id}")
        print(f"   Status: {result.status}")
        print(f"   Message: {result.message}")
        print(f"   From: {result.from_account}")
        print(f"   To: {result.to_account}")
        print(f"   Amount: ${result.amount:.2f}")

        return 0

    except Exception as e:
        print(f"\n❌ Transfer Failed: {e}")
        return 1


def handle_validate(client: BankingClient, args: argparse.Namespace) -> int:
    """Handle validate command."""
    try:
        print(f"🔍 Validating account {args.account}...")

        result = client.validate_account(args.account)

        print(f"\n✅ Validation Result:")
        print(f"   Account ID: {result.get('accountId')}")
        print(f"   Valid: {result.get('isValid')}")
        print(f"   Type: {result.get('accountType')}")
        print(f"   Status: {result.get('status')}")

        if 'bonusPoints' in result:
            print(f"   💡 Hint: {result.get('bonusPoints')}")

        return 0

    except Exception as e:
        print(f"\n❌ Validation Failed: {e}")
        return 1


def handle_balance(client: BankingClient, args: argparse.Namespace) -> int:
    """Handle balance command."""
    try:
        print(f"💰 Getting balance for account {args.account}...")

        result = client.get_balance(args.account, use_auth=args.auth)

        print(f"\n✅ Balance Information:")
        print(f"   Account ID: {result.get('accountId')}")
        print(f"   Balance: ${result.get('balance', 0):.2f}")
        print(f"   Currency: {result.get('currency', 'USD')}")

        return 0

    except Exception as e:
        print(f"\n❌ Get Balance Failed: {e}")
        return 1


def handle_list_accounts(client: BankingClient, args: argparse.Namespace) -> int:
    """Handle list-accounts command."""
    try:
        print("📋 Listing all accounts...")

        result = client.list_accounts(use_auth=args.auth)

        accounts = result.get('accounts', [])
        print(f"\n✅ Found {len(accounts)} accounts:")

        for i, account in enumerate(accounts, 1):
            print(f"\n   {i}. {account.get('accountId')}")
            print(f"      Type: {account.get('accountType')}")
            print(f"      Status: {account.get('status')}")
            if 'balance' in account:
                print(f"      Balance: ${account.get('balance', 0):.2f}")

        return 0

    except Exception as e:
        print(f"\n❌ List Accounts Failed: {e}")
        return 1


def handle_history(client: BankingClient, args: argparse.Namespace) -> int:
    """Handle history command."""
    try:
        print(f"🔐 Authenticating as {args.username}...")
        client.authenticate(username=args.username, password=args.password, scope="transfer")

        print("📜 Getting transaction history...")

        result = client.get_transaction_history()

        transactions = result.get('transactions', [])
        print(f"\n✅ Found {len(transactions)} transactions:")

        for i, tx in enumerate(transactions, 1):
            print(f"\n   {i}. Transaction ID: {tx.get('transactionId')}")
            print(f"      From: {tx.get('fromAccount')} → To: {tx.get('toAccount')}")
            print(f"      Amount: ${tx.get('amount', 0):.2f}")
            print(f"      Status: {tx.get('status')}")
            if 'timestamp' in tx:
                print(f"      Time: {tx.get('timestamp')}")

        return 0

    except Exception as e:
        print(f"\n❌ Get History Failed: {e}")
        return 1


def handle_auth(client: BankingClient, args: argparse.Namespace) -> int:
    """Handle auth command."""
    try:
        print(f"🔐 Authenticating as {args.username} with scope '{args.scope}'...")

        token = client.authenticate(
            username=args.username,
            password=args.password,
            scope=args.scope
        )

        print("\n✅ Authentication Successful!")
        print(f"   Token: {token[:50]}..." if len(token) > 50 else f"   Token: {token}")
        print(f"   Scope: {args.scope}")

        return 0

    except Exception as e:
        print(f"\n❌ Authentication Failed: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = setup_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create client with custom URL and timeout
    config = BankingConfig(
        api_base_url=args.url,
        api_timeout=args.timeout
    )

    with BankingClient(base_url=config.api_base_url, timeout=config.api_timeout) as client:
        # Route to appropriate handler
        if args.command == "transfer":
            return handle_transfer(client, args)
        elif args.command == "validate":
            return handle_validate(client, args)
        elif args.command == "balance":
            return handle_balance(client, args)
        elif args.command == "list-accounts":
            return handle_list_accounts(client, args)
        elif args.command == "history":
            return handle_history(client, args)
        elif args.command == "auth":
            return handle_auth(client, args)
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
            return 1


if __name__ == "__main__":
    sys.exit(main())
