#!/usr/bin/env python
"""
Competition Configuration Generator for ScoringEngine

This script generates YAML configuration files for ScoringEngine competitions.
It provides an interactive CLI for easy configuration creation.
"""

import argparse
import os
import sys
import yaml
from typing import Dict, List, Any


# Available check types and their default configurations
AVAILABLE_CHECKS = {
    'ICMP': {
        'check_name': 'ICMPCheck',
        'port': 0,
        'points': 25,
        'environments': [{'matching_content': '1 packets transmitted, 1 received'}]
    },
    'SSH': {
        'check_name': 'SSHCheck',
        'port': 22,
        'points': 150,
        'environments': [
            {
                'matching_content': '^SUCCESS',
                'properties': [{'name': 'commands', 'value': 'id;ls -l /home'}]
            },
            {
                'matching_content': 'PID',
                'properties': [{'name': 'commands', 'value': 'ps'}]
            }
        ],
        'requires_accounts': True
    },
    'HTTP': {
        'check_name': 'HTTPCheck',
        'port': 80,
        'points': 100,
        'environments': [{
            'matching_content': 'Thank you for using nginx',
            'properties': [
                {'name': 'useragent', 'value': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'},
                {'name': 'vhost', 'value': 'localhost'},
                {'name': 'uri', 'value': '/'}
            ]
        }]
    },
    'HTTPS': {
        'check_name': 'HTTPSCheck',
        'port': 443,
        'points': 100,
        'environments': [{
            'matching_content': 'Thank you for using nginx',
            'properties': [
                {'name': 'useragent', 'value': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'},
                {'name': 'vhost', 'value': 'localhost'},
                {'name': 'uri', 'value': '/'}
            ]
        }]
    },
    'FTP': {
        'check_name': 'FTPCheck',
        'port': 21,
        'points': 150,
        'environments': [{
            'matching_content': '^SUCCESS',
            'properties': [
                {'name': 'remotefilepath', 'value': '/ftp_files/testfile.txt'},
                {'name': 'filecontents', 'value': 'Sample file contents'}
            ]
        }],
        'requires_accounts': True
    },
    'DNS': {
        'check_name': 'DNSCheck',
        'port': 53,
        'points': 100,
        'environments': [{
            'matching_content': 'status: NOERROR',
            'properties': [
                {'name': 'qtype', 'value': 'A'},
                {'name': 'domain', 'value': 'example.com'}
            ]
        }]
    },
    'SMTP': {
        'check_name': 'SMTPCheck',
        'port': 25,
        'points': 100,
        'environments': [{
            'matching_content': 'Successfully sent email',
            'properties': [
                {'name': 'touser', 'value': 'recipient@example.com'},
                {'name': 'subject', 'value': 'Test Email'},
                {'name': 'body', 'value': 'This is a test email'}
            ]
        }],
        'requires_accounts': True
    },
    'SMTPS': {
        'check_name': 'SMTPSCheck',
        'port': 25,
        'points': 100,
        'environments': [{
            'matching_content': 'Successfully sent email',
            'properties': [
                {'name': 'touser', 'value': 'recipient@example.com'},
                {'name': 'subject', 'value': 'Test Email'},
                {'name': 'body', 'value': 'This is a test email'}
            ]
        }],
        'requires_accounts': True
    },
    'MySQL': {
        'check_name': 'MYSQLCheck',
        'port': 3306,
        'points': 100,
        'environments': [{
            'matching_content': 'USER_PRIVILEGES',
            'properties': [
                {'name': 'database', 'value': 'information_schema'},
                {'name': 'command', 'value': 'show tables;'}
            ]
        }],
        'requires_accounts': True
    },
    'MSSQL': {
        'check_name': 'MSSQLCheck',
        'port': 1433,
        'points': 100,
        'environments': [{
            'matching_content': 'Microsoft SQL Server',
            'properties': [
                {'name': 'database', 'value': 'master'},
                {'name': 'command', 'value': 'SELECT @@version;'}
            ]
        }],
        'requires_accounts': True
    },
    'PostgreSQL': {
        'check_name': 'POSTGRESQLCheck',
        'port': 5432,
        'points': 100,
        'environments': [{
            'matching_content': 'You are connected to database',
            'properties': [
                {'name': 'database', 'value': 'postgres'},
                {'name': 'command', 'value': '\\conninfo'}
            ]
        }],
        'requires_accounts': True
    },
    'SMB': {
        'check_name': 'SMBCheck',
        'port': 445,
        'points': 100,
        'environments': [{
            'matching_content': '^SUCCESS',
            'properties': [
                {'name': 'remote_name', 'value': 'DC'},
                {'name': 'share', 'value': 'SHARE'},
                {'name': 'file', 'value': 'flag.txt'},
                {'name': 'hash', 'value': 'b10d4d79a2bbdd3b120a6d7fbcaea5f0d6708e56c10eef021d02052abfaa271b'}
            ]
        }],
        'requires_accounts': True
    },
    'RDP': {
        'check_name': 'RDPCheck',
        'port': 3389,
        'points': 100,
        'environments': [{'matching_content': 'SUCCESS$'}],
        'requires_accounts': True
    },
    'WinRM': {
        'check_name': 'WinRMCheck',
        'port': 0,
        'points': 100,
        'environments': [{
            'matching_content': '^SUCCESS',
            'properties': [
                {'name': 'commands', 'value': 'ipconfig /all;whoami'}
            ]
        }],
        'requires_accounts': True
    },
    'LDAP': {
        'check_name': 'LDAPCheck',
        'port': 389,
        'points': 50,
        'environments': [{
            'matching_content': '^result: 0 Success',
            'properties': [
                {'name': 'domain', 'value': 'example.com'},
                {'name': 'base_dn', 'value': 'dc=example,dc=com'}
            ]
        }],
        'requires_accounts': True
    },
    'Elasticsearch': {
        'check_name': 'ElasticsearchCheck',
        'port': 9200,
        'points': 100,
        'environments': [{
            'matching_content': '^SUCCESS',
            'properties': [
                {'name': 'index', 'value': 'messages'},
                {'name': 'doc_type', 'value': 'sample_message'}
            ]
        }]
    },
}


def create_service(service_type: str, host: str, team_number: int = None,
                   username: str = None, password: str = None) -> Dict[str, Any]:
    """
    Create a service configuration based on the service type.

    Args:
        service_type: Type of service check (e.g., 'SSH', 'HTTP')
        host: Hostname or IP address
        team_number: Optional team number for IP substitution
        username: Optional username for services requiring accounts
        password: Optional password for services requiring accounts

    Returns:
        Dictionary containing service configuration
    """
    if service_type not in AVAILABLE_CHECKS:
        raise ValueError(f"Unknown service type: {service_type}")

    template = AVAILABLE_CHECKS[service_type].copy()

    service = {
        'name': service_type,
        'check_name': template['check_name'],
        'host': host,
        'port': template['port'],
        'points': template['points'],
        'environments': template['environments']
    }

    # Add accounts if required and credentials provided
    if template.get('requires_accounts') and username and password:
        service['accounts'] = [{'username': username, 'password': password}]

    return service


def generate_config(num_teams: int = 10,
                    services: List[str] = None,
                    base_network: str = '192.168',
                    team_password: str = 'CHANGEME',
                    admin_password: str = 'CHANGEME',
                    service_username: str = 'administrator',
                    service_password: str = 'CHANGEME') -> Dict[str, Any]:
    """
    Generate a competition configuration.

    Args:
        num_teams: Number of blue teams
        services: List of service types to include
        base_network: Base network for team subnets (e.g., '192.168')
        team_password: Default password for team login accounts
        admin_password: Default password for admin accounts
        service_username: Default username for service checks
        service_password: Default password for service checks

    Returns:
        Dictionary containing complete competition configuration
    """
    config = {'teams': []}

    # Add White Team
    config['teams'].append({
        'name': 'WhiteTeam',
        'color': 'White',
        'users': [{'username': 'whiteteam', 'password': admin_password}]
    })

    # Add Red Team
    config['teams'].append({
        'name': 'RedTeam',
        'color': 'Red',
        'users': [{'username': 'redteam', 'password': admin_password}]
    })

    # Default services if none specified
    if services is None:
        services = ['ICMP', 'SSH', 'HTTP']

    # Add Blue Teams
    for team_num in range(1, num_teams + 1):
        team = {
            'name': f'Team{team_num}',
            'color': 'Blue',
            'users': [{'username': f'team{team_num}', 'password': team_password}],
            'services': []
        }

        # Add services for this team
        for service_type in services:
            if service_type == 'ICMP':
                host = f'{base_network}.{team_num}.1'
            elif service_type in ['SSH', 'FTP', 'Telnet']:
                host = f'{base_network}.{team_num}.2'
            elif service_type in ['HTTP', 'HTTPS']:
                host = f'{base_network}.{team_num}.3'
            elif service_type in ['MySQL', 'PostgreSQL', 'MSSQL']:
                host = f'{base_network}.{team_num}.4'
            elif service_type == 'DNS':
                host = f'{base_network}.{team_num}.5'
            elif service_type in ['SMB', 'RDP', 'WinRM']:
                host = f'{base_network}.{team_num}.1'
            else:
                host = f'{base_network}.{team_num}.10'

            service = create_service(
                service_type,
                host,
                team_num,
                service_username,
                service_password
            )
            team['services'].append(service)

        config['teams'].append(team)

    return config


def interactive_mode():
    """Interactive mode for generating configuration."""
    print("=== ScoringEngine Configuration Generator ===\n")

    # Get number of teams
    while True:
        try:
            num_teams = int(input("Number of blue teams [10]: ") or "10")
            if num_teams < 1:
                print("Error: Must have at least 1 team")
                continue
            break
        except ValueError:
            print("Error: Please enter a valid number")

    # Get base network
    base_network = input("Base network (e.g., 192.168) [192.168]: ") or "192.168"

    # Get passwords
    team_password = input("Team login password [CHANGEME]: ") or "CHANGEME"
    admin_password = input("Admin (White/Red team) password [CHANGEME]: ") or "CHANGEME"

    # Get service credentials
    service_username = input("Service check username [administrator]: ") or "administrator"
    service_password = input("Service check password [CHANGEME]: ") or "CHANGEME"

    # Select services
    print("\nAvailable service types:")
    for i, service in enumerate(sorted(AVAILABLE_CHECKS.keys()), 1):
        print(f"  {i}. {service}")

    print("\nEnter service types to include (comma-separated) or 'all' for all services")
    print("Default services: ICMP,SSH,HTTP")
    service_input = input("Services: ").strip()

    if service_input.lower() == 'all':
        services = list(AVAILABLE_CHECKS.keys())
    elif service_input:
        services = [s.strip() for s in service_input.split(',')]
        # Validate services
        invalid = [s for s in services if s not in AVAILABLE_CHECKS]
        if invalid:
            print(f"Warning: Unknown services will be skipped: {', '.join(invalid)}")
            services = [s for s in services if s in AVAILABLE_CHECKS]
    else:
        services = ['ICMP', 'SSH', 'HTTP']

    # Get output file
    output_file = input("\nOutput file [competition.yaml]: ") or "competition.yaml"

    # Generate configuration
    print(f"\nGenerating configuration with {num_teams} teams and {len(services)} service types...")
    config = generate_config(
        num_teams=num_teams,
        services=services,
        base_network=base_network,
        team_password=team_password,
        admin_password=admin_password,
        service_username=service_username,
        service_password=service_password
    )

    # Write to file
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n✓ Configuration written to {output_file}")
    print(f"  - {len(config['teams'])} teams ({num_teams} blue teams)")
    print(f"  - {len(services)} service types per team")
    print(f"  - Total services: {num_teams * len(services)}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate ScoringEngine competition configuration files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended for first-time users)
  %(prog)s --interactive

  # Generate config with 15 teams, all services
  %(prog)s --teams 15 --services all -o competition.yaml

  # Generate config with specific services
  %(prog)s --teams 8 --services SSH,HTTP,HTTPS,MySQL,DNS

  # Custom network and passwords
  %(prog)s --teams 10 --base-network 10.0 --team-pass MyPass123

Available service types:
  """ + ', '.join(sorted(AVAILABLE_CHECKS.keys()))
    )

    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode (recommended)'
    )

    parser.add_argument(
        '-t', '--teams',
        type=int,
        default=10,
        metavar='N',
        help='Number of blue teams (default: 10)'
    )

    parser.add_argument(
        '-s', '--services',
        type=str,
        metavar='SERVICES',
        help='Comma-separated list of services or "all" (default: ICMP,SSH,HTTP)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='competition.yaml',
        metavar='FILE',
        help='Output file path (default: competition.yaml)'
    )

    parser.add_argument(
        '--base-network',
        type=str,
        default='192.168',
        metavar='NET',
        help='Base network for team subnets (default: 192.168)'
    )

    parser.add_argument(
        '--team-pass',
        type=str,
        default='CHANGEME',
        metavar='PASS',
        help='Default password for team accounts (default: CHANGEME)'
    )

    parser.add_argument(
        '--admin-pass',
        type=str,
        default='CHANGEME',
        metavar='PASS',
        help='Default password for admin accounts (default: CHANGEME)'
    )

    parser.add_argument(
        '--service-user',
        type=str,
        default='administrator',
        metavar='USER',
        help='Default username for service checks (default: administrator)'
    )

    parser.add_argument(
        '--service-pass',
        type=str,
        default='CHANGEME',
        metavar='PASS',
        help='Default password for service checks (default: CHANGEME)'
    )

    parser.add_argument(
        '--list-services',
        action='store_true',
        help='List all available service types and exit'
    )

    args = parser.parse_args()

    # List services and exit
    if args.list_services:
        print("Available service types:")
        for service in sorted(AVAILABLE_CHECKS.keys()):
            template = AVAILABLE_CHECKS[service]
            accounts = " (requires accounts)" if template.get('requires_accounts') else ""
            print(f"  {service:20s} - Port {template['port']:5d}, {template['points']:3d} points{accounts}")
        return 0

    # Interactive mode
    if args.interactive:
        try:
            interactive_mode()
            return 0
        except KeyboardInterrupt:
            print("\n\nCancelled by user")
            return 1

    # Non-interactive mode
    if args.services and args.services.lower() == 'all':
        services = list(AVAILABLE_CHECKS.keys())
    elif args.services:
        services = [s.strip() for s in args.services.split(',')]
        # Validate services
        invalid = [s for s in services if s not in AVAILABLE_CHECKS]
        if invalid:
            print(f"Error: Unknown service types: {', '.join(invalid)}", file=sys.stderr)
            print(f"Use --list-services to see available types", file=sys.stderr)
            return 1
    else:
        services = ['ICMP', 'SSH', 'HTTP']

    # Generate configuration
    print(f"Generating configuration with {args.teams} teams and {len(services)} service types...")
    config = generate_config(
        num_teams=args.teams,
        services=services,
        base_network=args.base_network,
        team_password=args.team_pass,
        admin_password=args.admin_pass,
        service_username=args.service_user,
        service_password=args.service_pass
    )

    # Write to file
    with open(args.output, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Configuration written to {args.output}")
    print(f"  - {len(config['teams'])} teams ({args.teams} blue teams)")
    print(f"  - {len(services)} service types per team")
    print(f"  - Total services: {args.teams * len(services)}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
