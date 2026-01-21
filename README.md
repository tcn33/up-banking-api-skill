# Up Banking API Skill

An AI agent skill for interacting with the [Up Banking API](https://developer.up.com.au/). Query accounts, transactions, categories, and tags.

## Installation

### Via [skills.sh](https://skills.sh/)

`npx skills add tcn33/up-banking-api-skill`

### Manual installation

Clone the repo: `git clone https://github.com/tcn33/up-banking-api-skill.git ~/.claude/skills/up-api`.

Alternative: Download the ZIP and extract to `~/.claude/skills/up-api`.

## Setup

### 1. Get your API token

1. Open the Up app on your phone
2. Go to Profile > Manage > Developer > Personal Access Tokens
3. Create a new token

### 2. Set the environment variable

```bash
export UP_API_TOKEN="up:yeah:xxxxxxxxxxxxx"
```

Add this to your shell profile (`~/.zshrc` or `~/.bashrc`) for persistence.

### 3. Verify setup

```bash
python3 scripts/up_api.py ping
```

You should see a status message with an emoji and UUID.

## Usage

All listing commands support `--json` for raw JSON output.

### Accounts

```bash
# List all accounts
python3 scripts/up_api.py accounts

# Filter by type (saver, transactional, home_loan)
python3 scripts/up_api.py accounts --type saver

# Filter by ownership (individual, joint)
python3 scripts/up_api.py accounts --ownership joint

# Get specific account details
python3 scripts/up_api.py account <account_id>
```

### Transactions

```bash
# Recent transactions (default 30)
python3 scripts/up_api.py transactions

# Limit results
python3 scripts/up_api.py transactions --limit 10

# Filter by date range (RFC-3339 format required)
python3 scripts/up_api.py transactions --since 2024-01-01T00:00:00Z --until 2024-02-01T00:00:00Z

# Filter by status
python3 scripts/up_api.py transactions --status settled
python3 scripts/up_api.py transactions --status held

# Filter by category
python3 scripts/up_api.py transactions --category groceries

# Filter by tag
python3 scripts/up_api.py transactions --tag "Coffee"

# Filter by account
python3 scripts/up_api.py transactions --account <account_id>

# Fetch all pages (for large date ranges)
python3 scripts/up_api.py transactions --all --since 2024-01-01T00:00:00Z

# Get specific transaction details
python3 scripts/up_api.py transaction <transaction_id>
```

### Categories

```bash
# List all categories
python3 scripts/up_api.py categories

# List subcategories of a parent
python3 scripts/up_api.py categories --parent good-life

# Set transaction category
python3 scripts/up_api.py categorize <transaction_id> <category_id>

# Clear transaction category
python3 scripts/up_api.py categorize <transaction_id> none
```

### Tags

```bash
# List all tags
python3 scripts/up_api.py tags

# Add tags to a transaction
python3 scripts/up_api.py tag <transaction_id> "Coffee" "Work"

# Remove tags from a transaction
python3 scripts/up_api.py untag <transaction_id> "Coffee"
```

### Webhooks

```bash
# List webhooks
python3 scripts/up_api.py webhooks

# Create a webhook
python3 scripts/up_api.py webhook-create https://example.com/hook "My webhook"

# Test a webhook
python3 scripts/up_api.py webhook-ping <webhook_id>

# View webhook delivery logs
python3 scripts/up_api.py webhook-logs <webhook_id>

# Delete a webhook
python3 scripts/up_api.py webhook-delete <webhook_id>
```

## JSON Output

Use `--json` with any listing command to get raw JSON for processing:

```bash
# Get all January transactions as JSON
python3 scripts/up_api.py transactions --json --all \
  --since 2024-01-01T00:00:00Z \
  --until 2024-02-01T00:00:00Z

# Pipe to jq for analysis
python3 scripts/up_api.py transactions --json --category groceries | \
  jq '[.[].attributes.amount.value | tonumber] | add'
```

## Date Format

The Up API requires RFC-3339 format for date filters:

- `2024-01-15T00:00:00Z` (UTC)
- `2024-01-15T00:00:00+11:00` (with timezone offset)

Simple date strings like `2024-01-15` will not work.

## Files

- `scripts/up_api.py` - CLI tool
- `skill.md` - Skill definition for AI agents
- `references/api-reference.md` - API endpoint reference

## Resources

- [Up API Documentation](https://developer.up.com.au/)
- [Up API GitHub](https://github.com/up-banking/api)
