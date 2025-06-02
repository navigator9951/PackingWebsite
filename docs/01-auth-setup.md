# Authentication Setup Guide

## Overview

The Packing Website uses store-level authentication with automatically generated 3-word passwords (like "happy-tiger-blue"). Each store has its own password for accessing the price editor. These passwords use common, memorable words from the EFF Special wordlist for easy typing.

**Password Flexibility**: Passwords are normalized for user convenience. You can enter them in any format - "Happy-Tiger-Blue", "happy tiger blue", or "HAPPY TIGER BLUE" will all work. Only the letters matter, not the case or separators.

## Initial Setup

### Create Authentication for New Stores

**Prerequisites**: The store YAML file (e.g., `stores/store1.yml`) must exist before creating authentication.

```bash
# Generate automatic password (outputs to stdout)
./tools/auth create 1

# Create with custom password (superadmin only)
./tools/auth create 1 --password "MyCustomP@ssw0rd!"
```

**What happens:**

1. Checks if `stores/store1.yml` exists (fails if not)
2. Checks if store already has auth (prompts for confirmation if yes)
3. Generates/normalizes password (this makes user typos [caps lock, whitespace, etc] a non-factor)
4. **Outputs password to stdout** for user to save
5. Stores hashed password in database

**Password Examples:**

- Generated output: `Password: happy-tiger-blue`
- Custom input: `DHSdsu21723$$2_q!` → Output: `Normalized: dhsdsuq` (we frown upon the use of --password If the user wants to get any real entropy from this, better use a LOOOOONG password)

**IMPORTANT**: Save passwords immediately! They cannot be recovered.

## Superadmin Operations

**Quick Reference:**

- **(a) Create New Store**: `./tools/auth create {store_id}` (requires stores/store{id}.yml)
- **(b) Remove Store**: Not currently implemented - passwords persist once created
- **(c) Update Password**: `./tools/auth update {store_id}`

**Notes:**

- All commands output passwords to stdout
- Store YAML files must exist before creating auth
- Existing stores prompt for confirmation unless using --force

### Create or Update Store Password

Creating a new store and updating an existing store use the same command:

```bash
# Create new store or update existing (will prompt for confirmation)
./tools/auth create 1

# Update existing store password
./tools/auth update 1

# Update with custom password
./tools/auth update 1 --password "MyCustomP@ss"
```

### Remove Store Authentication

**Note**: There is currently no dedicated remove command. To effectively disable authentication for a store:

1. You can let the password exist but not use it
2. Or blow away/re-init the entire database (removes ALL passwords)

## Managing Passwords

### Update/Reset Store Password

See "Create or Update Store Password" above - it's the same operation.

### List All Stores with Auth

```bash
./tools/auth list
```

Shows all stores that have passwords configured.

### Verify a Password

```bash
./tools/auth verify 1
```

Prompts for the password and verifies it's correct.

### View Audit Log

```bash
# All stores
./tools/auth audit

# Specific store
./tools/auth audit --store 1

# Last 100 entries
./tools/auth audit --limit 100
```

## How It Works

1. **Password Generation**:
   - Default: Uses `xkcdpass` with EFF Special wordlist to generate memorable 3-word phrases
   - Custom: Superadmins can specify their own passwords with the `--password` flag
2. **Password Normalization**: All passwords (generated or custom) are normalized to lowercase letters only (a-z), ignoring case and non-letter characters
3. **Storage**: Normalized passwords are bcrypt-hashed in SQLite database
4. **Sessions**: 24-hour sessions created after successful login
5. **Audit Trail**: All login attempts and actions are logged

## Accessing the Price Editor

Once a store has a password:

1. Navigate to `/{store_id}/price_editor`
2. Enter the store password when prompted
3. Session lasts 24 hours
4. Logout available from the editor interface

## Security Notes

- Passwords are never stored in plain text
- Each store has its own password
- Sessions expire after 24 hours
- All access attempts are logged
- No password recovery - only reset
- 3-word passwords from EFF Special wordlist provide ~31 bits of entropy
- 1,296³ = ~2.2 billion possible combinations
- Adequate security for non-critical tool with audit logs

## Frontend Integration

### Core Authentication Library for client: `/lib/auth.js`

Include this library in any page that needs authentication. It provides:

- **Token management**: get/set/remove authentication tokens
- **API methods**: login, verify, check auth status
- **Authenticated requests**: helper for making authorized API calls
- **Page protection**: automatic redirects for unauthorized access

### Usage Examples

For any page that needs authentication:

```html
<!-- Include the auth library -->
<script src="/lib/auth.js"></script>

<script>
  const storeId = '1'; // Get from URL path

  // Option 1: Require authentication (redirects to login if not authenticated)
  AuthManager.requireAuth(storeId);

  // Option 2: Check auth status without redirect
  const status = await AuthManager.getAuthStatus(storeId);
  if (status.isAuthenticated) {
    // Show protected content
  }

  // Option 3: Make authenticated API calls
  const response = await AuthManager.makeAuthenticatedRequest(
    `/api/store/${storeId}/prices`,
    { method: 'GET' },
    storeId
  );
</script>
```

### Auth UI Components

The library also provides UI helper functions:

```javascript
// Add login/logout UI to any container
AuthManager.initAuthUI("auth-container", storeId);

// Manual logout
AuthManager.logout(storeId);
```

### Navigation Integration

The navigation component (`/components/navigation.js`) automatically integrates with AuthManager to show:

- Nothing if no auth configured
- "Login" link if auth required but not logged in
- "Authenticated" badge + logout button when logged in

```html
<div id="nav-container"></div>
<script src="/lib/auth.js"></script>
<script src="/components/navigation.js"></script>
<script>
  initAdminNav("nav-container", storeId, "prices");
</script>
```

## Troubleshooting

### "CRITICAL ERROR: xkcdpass IS NOT INSTALLED!"

There is NO fallback. You MUST install xkcdpass:

```bash
docker compose exec web pip install xkcdpass
```

The system will refuse to generate passwords without it.

**Tool Architecture:**

- `./tools/auth` (host) - Bash wrapper that automatically runs commands in Docker
- `tools/manage_auth.py` (container) - Python script that handles authentication operations

### Lost Password

There's no recovery mechanism. You must reset the password:

```bash
./tools/auth update {store_id}
```

### Database Issues

If the database is corrupted, restart the Docker container to reinitialize:

```bash
docker compose restart
```

Note: This will lose all existing passwords.

### Frontend Auth Issues

- **Token persists after logout**: Clear localStorage manually in browser console
- **Redirect loops**: Check if the API endpoints are returning correct status codes
- **Can't see auth UI**: Ensure `/lib/auth.js` is loaded before components
