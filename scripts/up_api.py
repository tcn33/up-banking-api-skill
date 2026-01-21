#!/usr/bin/env python3
"""
Up Banking API CLI tool.

Requires UP_API_TOKEN environment variable.

Usage:
    up_api.py ping                              # Test API connectivity
    up_api.py accounts [--type TYPE]            # List accounts
    up_api.py account <id>                      # Get account details
    up_api.py transactions [OPTIONS]            # List transactions
    up_api.py transaction <id>                  # Get transaction details
    up_api.py categorize <tx_id> <cat_id>       # Set transaction category
    up_api.py categories [--parent ID]          # List categories
    up_api.py tags                              # List all tags
    up_api.py tag <tx_id> <tag> [<tag>...]      # Add tags to transaction
    up_api.py untag <tx_id> <tag> [<tag>...]    # Remove tags from transaction
    up_api.py webhooks                          # List webhooks
    up_api.py webhook-create <url> [desc]       # Create webhook
    up_api.py webhook-delete <id>               # Delete webhook
    up_api.py webhook-ping <id>                 # Ping webhook
    up_api.py webhook-logs <id>                 # Get webhook logs
"""

import argparse
import json
import os
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

BASE_URL = "https://api.up.com.au/api/v1"


def get_token():
    token = os.environ.get("UP_API_TOKEN")
    if not token:
        print("Error: UP_API_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    return token


def api_request(method, endpoint, data=None, params=None):
    """Make an API request and return parsed JSON response."""
    url = f"{BASE_URL}{endpoint}"
    if params:
        url += "?" + urlencode(params, doseq=True)

    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode()
        try:
            error_data = json.loads(error_body)
            print(f"API Error {e.code}: {json.dumps(error_data, indent=2)}", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"API Error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)


def fetch_all_pages(endpoint, params=None, max_pages=None):
    """Fetch all pages of a paginated endpoint."""
    all_data = []
    page_count = 0

    result = api_request("GET", endpoint, params=params)
    all_data.extend(result.get("data", []))
    page_count += 1

    while result.get("links", {}).get("next") and (max_pages is None or page_count < max_pages):
        next_url = result["links"]["next"]
        # Extract path and query from full URL
        next_path = next_url.replace(BASE_URL, "")
        result = api_request("GET", next_path)
        all_data.extend(result.get("data", []))
        page_count += 1

    return all_data


def format_money(amount_obj):
    """Format money object as string."""
    if not amount_obj:
        return "N/A"
    return f"{amount_obj['currencyCode']} {amount_obj['value']}"


def format_date(iso_string):
    """Format ISO date string."""
    if not iso_string:
        return "N/A"
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M")


# Command handlers

def cmd_ping(args):
    result = api_request("GET", "/util/ping")
    meta = result.get("meta", {})
    print(f"Status: {meta.get('statusEmoji', '?')} {meta.get('id', 'unknown')}")


def cmd_accounts(args):
    params = {}
    if args.type:
        params["filter[accountType]"] = args.type.upper()
    if args.ownership:
        params["filter[ownershipType]"] = args.ownership.upper()

    accounts = fetch_all_pages("/accounts", params)

    if args.json:
        print(json.dumps(accounts, indent=2))
        return

    for acc in accounts:
        attrs = acc["attributes"]
        balance = format_money(attrs.get("balance"))
        print(f"{acc['id'][:8]}  {attrs['displayName']:30} {attrs['accountType']:15} {balance}")


def cmd_account(args):
    result = api_request("GET", f"/accounts/{args.id}")
    if args.json:
        print(json.dumps(result["data"], indent=2))
        return

    acc = result["data"]
    attrs = acc["attributes"]
    print(f"ID:          {acc['id']}")
    print(f"Name:        {attrs['displayName']}")
    print(f"Type:        {attrs['accountType']}")
    print(f"Ownership:   {attrs.get('ownershipType', 'N/A')}")
    print(f"Balance:     {format_money(attrs.get('balance'))}")
    print(f"Created:     {format_date(attrs.get('createdAt'))}")


def cmd_transactions(args):
    params = {"page[size]": str(args.limit)}

    if args.status:
        params["filter[status]"] = args.status.upper()
    if args.since:
        params["filter[since]"] = args.since
    if args.until:
        params["filter[until]"] = args.until
    if args.category:
        params["filter[category]"] = args.category
    if args.tag:
        params["filter[tag]"] = args.tag

    endpoint = f"/accounts/{args.account}/transactions" if args.account else "/transactions"

    if args.all:
        transactions = fetch_all_pages(endpoint, params)
    else:
        result = api_request("GET", endpoint, params=params)
        transactions = result.get("data", [])

    if args.json:
        print(json.dumps(transactions, indent=2))
        return

    for tx in transactions:
        attrs = tx["attributes"]
        amount = format_money(attrs.get("amount"))
        date = format_date(attrs.get("createdAt"))[:10]
        desc = attrs.get("description", "")[:40]
        status = "H" if attrs.get("status") == "HELD" else "S"
        print(f"{tx['id'][:8]}  {date}  {status}  {amount:>15}  {desc}")


def cmd_transaction(args):
    result = api_request("GET", f"/transactions/{args.id}")
    if args.json:
        print(json.dumps(result["data"], indent=2))
        return

    tx = result["data"]
    attrs = tx["attributes"]
    rels = tx.get("relationships", {})

    print(f"ID:          {tx['id']}")
    print(f"Status:      {attrs.get('status')}")
    print(f"Description: {attrs.get('description')}")
    print(f"Message:     {attrs.get('message') or 'N/A'}")
    print(f"Amount:      {format_money(attrs.get('amount'))}")
    if attrs.get("foreignAmount"):
        print(f"Foreign:     {format_money(attrs.get('foreignAmount'))}")
    print(f"Created:     {format_date(attrs.get('createdAt'))}")
    print(f"Settled:     {format_date(attrs.get('settledAt'))}")

    cat_data = rels.get("category", {}).get("data")
    if cat_data:
        print(f"Category:    {cat_data['id']}")

    tags_data = rels.get("tags", {}).get("data", [])
    if tags_data:
        print(f"Tags:        {', '.join(t['id'] for t in tags_data)}")


def cmd_categorize(args):
    data = {"data": {"type": "categories", "id": args.category_id} if args.category_id != "none" else None}
    api_request("PATCH", f"/transactions/{args.transaction_id}/relationships/category", data=data)
    print(f"Category {'cleared' if args.category_id == 'none' else 'set'} for transaction {args.transaction_id}")


def cmd_categories(args):
    params = {}
    if args.parent:
        params["filter[parent]"] = args.parent

    categories = fetch_all_pages("/categories", params)

    if args.json:
        print(json.dumps(categories, indent=2))
        return

    for cat in categories:
        attrs = cat["attributes"]
        parent = cat.get("relationships", {}).get("parent", {}).get("data")
        parent_id = parent["id"] if parent else "-"
        print(f"{cat['id']:30} {parent_id:20} {attrs['name']}")


def cmd_tags(args):
    tags = fetch_all_pages("/tags")

    if args.json:
        print(json.dumps(tags, indent=2))
        return

    for tag in tags:
        print(tag["id"])


def cmd_tag(args):
    data = {"data": [{"type": "tags", "id": tag} for tag in args.tags]}
    api_request("POST", f"/transactions/{args.transaction_id}/relationships/tags", data=data)
    print(f"Added tags to transaction {args.transaction_id}: {', '.join(args.tags)}")


def cmd_untag(args):
    data = {"data": [{"type": "tags", "id": tag} for tag in args.tags]}
    api_request("DELETE", f"/transactions/{args.transaction_id}/relationships/tags", data=data)
    print(f"Removed tags from transaction {args.transaction_id}: {', '.join(args.tags)}")


def cmd_webhooks(args):
    webhooks = fetch_all_pages("/webhooks")

    if args.json:
        print(json.dumps(webhooks, indent=2))
        return

    for wh in webhooks:
        attrs = wh["attributes"]
        print(f"{wh['id'][:8]}  {attrs['url'][:50]}  {attrs.get('description', '')[:20]}")


def cmd_webhook_create(args):
    data = {"data": {"attributes": {"url": args.url, "description": args.description}}}
    result = api_request("POST", "/webhooks", data=data)

    wh = result["data"]
    attrs = wh["attributes"]
    print(f"Created webhook: {wh['id']}")
    print(f"URL: {attrs['url']}")
    print(f"Secret: {attrs['secretKey']}")
    print("\nIMPORTANT: Save the secret key - it won't be shown again!")


def cmd_webhook_delete(args):
    api_request("DELETE", f"/webhooks/{args.id}")
    print(f"Deleted webhook {args.id}")


def cmd_webhook_ping(args):
    result = api_request("POST", f"/webhooks/{args.id}/ping")
    event = result["data"]
    attrs = event["attributes"]
    print(f"Ping sent: {event['id']}")
    print(f"Delivery status: {attrs.get('deliveryStatus')}")


def cmd_webhook_logs(args):
    result = api_request("GET", f"/webhooks/{args.id}/logs")
    logs = result.get("data", [])

    if args.json:
        print(json.dumps(logs, indent=2))
        return

    for log in logs:
        attrs = log["attributes"]
        print(f"{log['id'][:8]}  {attrs.get('deliveryStatus'):10}  {format_date(attrs.get('createdAt'))}")


def main():
    parser = argparse.ArgumentParser(description="Up Banking API CLI")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ping
    subparsers.add_parser("ping", help="Test API connectivity")

    # accounts
    p = subparsers.add_parser("accounts", help="List accounts")
    p.add_argument("--type", choices=["saver", "transactional", "home_loan"], help="Filter by account type")
    p.add_argument("--ownership", choices=["individual", "joint"], help="Filter by ownership type")
    p.add_argument("--json", action="store_true", help="Output raw JSON")

    # account
    p = subparsers.add_parser("account", help="Get account details")
    p.add_argument("id", help="Account ID")
    p.add_argument("--json", action="store_true", help="Output raw JSON")

    # transactions
    p = subparsers.add_parser("transactions", help="List transactions")
    p.add_argument("--account", help="Filter by account ID")
    p.add_argument("--status", choices=["held", "settled"], help="Filter by status")
    p.add_argument("--since", help="Filter from date (ISO 8601)")
    p.add_argument("--until", help="Filter to date (ISO 8601)")
    p.add_argument("--category", help="Filter by category ID")
    p.add_argument("--tag", help="Filter by tag")
    p.add_argument("--limit", type=int, default=30, help="Number of transactions (default: 30)")
    p.add_argument("--all", action="store_true", help="Fetch all pages")
    p.add_argument("--json", action="store_true", help="Output raw JSON")

    # transaction
    p = subparsers.add_parser("transaction", help="Get transaction details")
    p.add_argument("id", help="Transaction ID")
    p.add_argument("--json", action="store_true", help="Output raw JSON")

    # categorize
    p = subparsers.add_parser("categorize", help="Set transaction category")
    p.add_argument("transaction_id", help="Transaction ID")
    p.add_argument("category_id", help="Category ID (or 'none' to clear)")

    # categories
    p = subparsers.add_parser("categories", help="List categories")
    p.add_argument("--parent", help="Filter by parent category ID")
    p.add_argument("--json", action="store_true", help="Output raw JSON")

    # tags
    p = subparsers.add_parser("tags", help="List all tags")
    p.add_argument("--json", action="store_true", help="Output raw JSON")

    # tag
    p = subparsers.add_parser("tag", help="Add tags to transaction")
    p.add_argument("transaction_id", help="Transaction ID")
    p.add_argument("tags", nargs="+", help="Tags to add")

    # untag
    p = subparsers.add_parser("untag", help="Remove tags from transaction")
    p.add_argument("transaction_id", help="Transaction ID")
    p.add_argument("tags", nargs="+", help="Tags to remove")

    # webhooks
    p = subparsers.add_parser("webhooks", help="List webhooks")
    p.add_argument("--json", action="store_true", help="Output raw JSON")

    # webhook-create
    p = subparsers.add_parser("webhook-create", help="Create webhook")
    p.add_argument("url", help="Webhook URL")
    p.add_argument("description", nargs="?", default="", help="Description")

    # webhook-delete
    p = subparsers.add_parser("webhook-delete", help="Delete webhook")
    p.add_argument("id", help="Webhook ID")

    # webhook-ping
    p = subparsers.add_parser("webhook-ping", help="Ping webhook")
    p.add_argument("id", help="Webhook ID")

    # webhook-logs
    p = subparsers.add_parser("webhook-logs", help="Get webhook logs")
    p.add_argument("id", help="Webhook ID")
    p.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    commands = {
        "ping": cmd_ping,
        "accounts": cmd_accounts,
        "account": cmd_account,
        "transactions": cmd_transactions,
        "transaction": cmd_transaction,
        "categorize": cmd_categorize,
        "categories": cmd_categories,
        "tags": cmd_tags,
        "tag": cmd_tag,
        "untag": cmd_untag,
        "webhooks": cmd_webhooks,
        "webhook-create": cmd_webhook_create,
        "webhook-delete": cmd_webhook_delete,
        "webhook-ping": cmd_webhook_ping,
        "webhook-logs": cmd_webhook_logs,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
