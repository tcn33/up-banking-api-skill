# Up Banking API Reference

Base URL: `https://api.up.com.au/api/v1`

## Authentication

All requests require `Authorization: Bearer $UP_API_TOKEN` header.

## Endpoints

### Utility

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/util/ping` | GET | Test connectivity and auth |

### Accounts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/accounts` | GET | List all accounts |
| `/accounts/{id}` | GET | Get account details |

**Filters for `/accounts`:**
- `filter[accountType]` - `SAVER`, `TRANSACTIONAL`, `HOME_LOAN`
- `filter[ownershipType]` - `INDIVIDUAL`, `JOINT`

**Account attributes:**
- `displayName` - Account name
- `accountType` - Type of account
- `ownershipType` - Individual or joint
- `balance` - Current balance (money object)
- `createdAt` - Creation timestamp

### Transactions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/transactions` | GET | List all transactions |
| `/transactions/{id}` | GET | Get transaction details |
| `/accounts/{id}/transactions` | GET | List transactions for account |
| `/transactions/{id}/relationships/category` | PATCH | Set category |
| `/transactions/{id}/relationships/tags` | POST | Add tags |
| `/transactions/{id}/relationships/tags` | DELETE | Remove tags |

**Filters for transactions:**
- `filter[status]` - `HELD`, `SETTLED`
- `filter[since]` - RFC-3339 datetime, e.g. `2024-01-01T00:00:00Z` (inclusive)
- `filter[until]` - RFC-3339 datetime, e.g. `2024-02-01T00:00:00Z` (exclusive)
- `filter[category]` - Category ID
- `filter[tag]` - Tag name
- `page[size]` - Results per page (max ~100)

**Transaction attributes:**
- `status` - `HELD` or `SETTLED`
- `rawText` - Raw transaction text (may be null)
- `description` - Human-readable description
- `message` - Optional message (transfers)
- `amount` - Transaction amount (money object, negative = debit)
- `foreignAmount` - Original currency if foreign (money object)
- `settledAt` - Settlement timestamp (null if held)
- `createdAt` - Creation timestamp

**Relationships:**
- `account` - Associated account
- `category` - Assigned category (can be null)
- `parentCategory` - Parent category
- `tags` - List of tags (max 6)

### Categories

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/categories` | GET | List all categories |
| `/categories/{id}` | GET | Get category details |

**Filters:**
- `filter[parent]` - Parent category ID

**Category attributes:**
- `name` - Display name

**Relationships:**
- `parent` - Parent category (null for top-level)
- `children` - Child categories

### Tags

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tags` | GET | List all tags |

Tags are user-defined labels. Maximum 6 tags per transaction.

### Webhooks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhooks` | GET | List webhooks |
| `/webhooks` | POST | Create webhook |
| `/webhooks/{id}` | GET | Get webhook details |
| `/webhooks/{id}` | DELETE | Delete webhook |
| `/webhooks/{id}/ping` | POST | Test webhook |
| `/webhooks/{id}/logs` | GET | Get delivery logs |

**Limits:** Maximum 10 active webhooks.

**Webhook attributes:**
- `url` - Delivery URL
- `description` - Optional description
- `secretKey` - HMAC signing key (only on creation)
- `createdAt` - Creation timestamp

**Events:**
- `TRANSACTION_CREATED` - New transaction
- `TRANSACTION_SETTLED` - Transaction settled
- `TRANSACTION_DELETED` - Transaction removed

**Signature verification:**
Webhooks include `X-Up-Authenticity-Signature` header with HMAC-SHA256 signature of the request body using the secret key.

## Data Types

### Money Object
```json
{
  "currencyCode": "AUD",
  "value": "-10.50",
  "valueInBaseUnits": -1050
}
```

### Pagination
Responses include `links.prev` and `links.next` for cursor-based pagination. Follow links until null.

## Rate Limiting

- HTTP 429 when rate limited
- Check `X-RateLimit-Remaining` header
- Use exponential backoff

## Common Category IDs

Top-level categories:
- `good-life` - Entertainment, lifestyle
- `home` - Household expenses
- `personal` - Personal care, health
- `transport` - Vehicle, public transport

Common subcategories:
- `groceries` - Food shopping (parent: `home`)
- `restaurants-and-cafes` - Dining out (parent: `good-life`)
- `takeaway` - Takeaway food (parent: `good-life`)
- `fuel` - Vehicle fuel (parent: `transport`)

Use `categories --parent <id>` to see all subcategories.
