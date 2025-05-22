#!/usr/bin/env python3
"""
Authentication Management Tool

This is the OFFICIAL tool for managing store authentication in Packing Website.
Use this tool for all auth-related operations:
- Initializing the authentication database
- Creating store authentication
- Updating passwords
- Verifying passwords
- Listing stores with authentication
- Viewing audit logs

Examples:
    # Using the convenience script (runs inside Docker):
    ./tools/auth init
    ./tools/auth create 1
    ./tools/auth update 1
    ./tools/auth list
    ./tools/auth verify 1
    ./tools/auth audit
    
Note: This tool should be run inside the Docker container. The convenience script
./tools/auth handles this automatically.
"""

import sys
import os
import argparse
import getpass
from tabulate import tabulate
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.auth_manager import (
    init_db, create_store_auth, list_stores, 
    get_audit_log, verify_store_password
)

def cmd_init(args):
    """Initialize the database"""
    init_db()
    print("Database initialized successfully.")

def cmd_create(args):
    """Create store authentication"""
    store_id = args.store
    
    # Check if store YAML file exists
    yaml_path = Path(f"stores/store{store_id}.yml")
    if not yaml_path.exists():
        print(f"Error: Store configuration file 'stores/store{store_id}.yml' not found!")
        print(f"Please create the store configuration file before setting up authentication.")
        return
    
    # Check if this store already has authentication
    stores = list_stores()
    if any(s['store_id'] == store_id for s in stores):
        print(f"Error: Store {store_id} already has authentication configured.")
        print(f"Use './tools/auth update {store_id}' to update the password.")
        return
    
    # Generate password
    password = create_store_auth(store_id, password=args.password)
    
    print(f"\nCreated authentication for store {store_id}")
    print(f"Password: {password}")
    if args.password:
        from lib.auth_manager import normalize_password
        normalized = normalize_password(args.password)
        print(f"Normalized: {normalized} (only lowercase a-z characters)")
    print("\nIMPORTANT: Save this password securely. It cannot be recovered!")

def cmd_update(args):
    """Update store authentication password"""
    store_id = args.store
    
    # Check if store YAML file exists
    yaml_path = Path(f"stores/store{store_id}.yml")
    if not yaml_path.exists():
        print(f"Error: Store configuration file 'stores/store{store_id}.yml' not found!")
        return
    
    # Check if this store has authentication
    stores = list_stores()
    if not any(s['store_id'] == store_id for s in stores):
        print(f"Error: Store {store_id} does not have authentication configured.")
        print(f"Use './tools/auth create {store_id}' to create authentication first.")
        return
    
    # Confirm update
    if not args.force:
        response = input(f"Update password for store {store_id}? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            return
    
    # Generate new password
    password = create_store_auth(store_id, password=args.password)
    
    print(f"\nUpdated authentication for store {store_id}")
    print(f"Password: {password}")
    if args.password:
        from lib.auth_manager import normalize_password
        normalized = normalize_password(args.password)
        print(f"Normalized: {normalized} (only lowercase a-z characters)")
    print("\nIMPORTANT: Save this password securely. It cannot be recovered!")

def cmd_list(args):
    """List all stores with authentication"""
    stores = list_stores()
    
    if not stores:
        print("No stores configured.")
        return
    
    # Format the data for tabulate
    table_data = []
    for store in stores:
        table_data.append([
            store['store_id'],
            store['created_at'],
            store['updated_at']
        ])
    
    headers = ['Store ID', 'Created', 'Last Updated']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))

def cmd_verify(args):
    """Verify a store password"""
    store_id = args.store
    
    # Prompt for password
    password = getpass.getpass("Enter password: ")
    
    if verify_store_password(store_id, password):
        print("✓ Password correct")
    else:
        print("✗ Invalid password")
        sys.exit(1)

def cmd_audit(args):
    """Show audit log"""
    logs = get_audit_log(store_id=args.store, limit=args.limit)
    
    if not logs:
        print("No audit log entries found.")
        return
    
    # Format the data for tabulate
    table_data = []
    for log in logs:
        table_data.append([
            log['timestamp'],
            log['store_id'],
            log['action'],
            log.get('details', '')
        ])
    
    headers = ['Timestamp', 'Store', 'Action', 'Details']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))

def main():
    parser = argparse.ArgumentParser(
        description='Manage store authentication for Packing Website'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init command
    parser_init = subparsers.add_parser('init', help='Initialize the database')
    parser_init.set_defaults(func=cmd_init)
    
    # create command
    parser_create = subparsers.add_parser(
        'create', 
        help='Create store authentication'
    )
    parser_create.add_argument('store', help='Store ID (e.g., 1, 2, 3)')
    parser_create.add_argument(
        '-p', '--password',
        help='Specify custom password (superadmin only, will be normalized to lowercase a-z)'
    )
    parser_create.set_defaults(func=cmd_create)
    
    # update command
    parser_update = subparsers.add_parser(
        'update', 
        help='Update store authentication password'
    )
    parser_update.add_argument('store', help='Store ID (e.g., 1, 2, 3)')
    parser_update.add_argument(
        '-f', '--force', 
        action='store_true',
        help='Force update without confirmation'
    )
    parser_update.add_argument(
        '-p', '--password',
        help='Specify custom password (superadmin only, will be normalized to lowercase a-z)'
    )
    parser_update.set_defaults(func=cmd_update)
    
    # list command
    parser_list = subparsers.add_parser('list', help='List all stores')
    parser_list.set_defaults(func=cmd_list)
    
    # verify command
    parser_verify = subparsers.add_parser(
        'verify', 
        help='Verify a store password'
    )
    parser_verify.add_argument('store', help='Store ID')
    parser_verify.set_defaults(func=cmd_verify)
    
    # audit command
    parser_audit = subparsers.add_parser('audit', help='Show audit log')
    parser_audit.add_argument(
        '-s', '--store', 
        help='Filter by store ID'
    )
    parser_audit.add_argument(
        '-l', '--limit', 
        type=int, 
        default=50,
        help='Number of entries to show (default: 50)'
    )
    parser_audit.set_defaults(func=cmd_audit)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the command
    args.func(args)

if __name__ == "__main__":
    main()