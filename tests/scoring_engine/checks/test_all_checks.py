"""
Parametrized test covering all service check command generation.

Replaces the 28 individual test_*.py files that each contained a single
``CheckTest`` subclass.  Each check is a ``pytest.param`` entry — the
test sets up a Service/Environment with the given properties and accounts,
instantiates the check via ``Engine.check_name_to_obj()``, and asserts the
generated command matches.
"""

import pytest

from scoring_engine.db import db
from scoring_engine.engine.basic_check import CHECKS_BIN_PATH
from scoring_engine.engine.engine import Engine
from scoring_engine.models.account import Account
from scoring_engine.models.environment import Environment
from scoring_engine.models.property import Property
from scoring_engine.models.service import Service

P = CHECKS_BIN_PATH

# (check_name, properties, accounts, expected_cmd)
CHECK_PARAMS = [
    pytest.param(
        "AgentCheck",
        {},
        {},
        P + "/agent_check 127.0.0.1",
        id="AgentCheck",
    ),
    pytest.param(
        "DNSCheck",
        {"qtype": "A", "domain": "www.google.com"},
        {},
        "dig +noedns @127.0.0.1 -p 1234 -t A -q www.google.com",
        id="DNSCheck",
    ),
    pytest.param(
        "ElasticsearchCheck",
        {"index": "events", "doc_type": "message"},
        {},
        P + "/elasticsearch_check 127.0.0.1 1234 events message",
        id="ElasticsearchCheck",
    ),
    pytest.param(
        "FTPCheck",
        {"remotefilepath": "/adir/textfile.txt", "filecontents": "Sample contents"},
        {"testuser": "testpass"},
        f"{P}/ftp_check 127.0.0.1 1234 testuser testpass /adir/textfile.txt 'Sample contents'",
        id="FTPCheck",
    ),
    pytest.param(
        "HTTPCheck",
        {"useragent": "testagent", "vhost": "www.example.com", "uri": "/index.html"},
        {},
        "curl -s -S -4 -v -L --cookie-jar - --header 'Host: www.example.com' -A testagent 127.0.0.1:1234/index.html",
        id="HTTPCheck",
    ),
    pytest.param(
        "HTTPSCheck",
        {"useragent": "testagent", "vhost": "www.example.com", "uri": "/index.html"},
        {},
        "curl -s -S -4 -v -L --cookie-jar - --ssl-reqd --insecure --header 'Host: www.example.com' -A testagent https://127.0.0.1:1234/index.html",
        id="HTTPSCheck",
    ),
    pytest.param(
        "ICMPCheck",
        {},
        {},
        "ping -c 1 127.0.0.1",
        id="ICMPCheck",
    ),
    pytest.param(
        "IMAPCheck",
        {"domain": "test.com"},
        {"testuser": "passtest"},
        "medusa -R 1 -h 127.0.0.1 -n 1234 -u testuser@test.com -p passtest -M imap -m AUTH:LOGIN",
        id="IMAPCheck",
    ),
    pytest.param(
        "IMAPSCheck",
        {"domain": "test.com"},
        {"testuser": "passtest"},
        "medusa -s -R 1 -h 127.0.0.1 -n 1234 -u testuser@test.com -p passtest -M imap -m AUTH:LOGIN",
        id="IMAPSCheck",
    ),
    pytest.param(
        "LDAPCheck",
        {"domain_base": "dc=example,dc=com"},
        {"testuser": "testpass"},
        "ldapsearch -x -H ldap://127.0.0.1:1234 -D cn=testuser,cn=Users,dc=example,dc=com -w testpass -b dc=example,dc=com '(objectclass=Domain)' cn",
        id="LDAPCheck",
    ),
    pytest.param(
        "MSSQLCheck",
        {"database": "master", "command": "SELECT @@version"},
        {"pwnbus": "pwnbuspass"},
        "SQLCMDPASSWORD=pwnbuspass sqlcmd -S 127.0.0.1,1234 -U pwnbus -d master -Q 'SELECT @@version'",
        id="MSSQLCheck",
    ),
    pytest.param(
        "MYSQLCheck",
        {"database": "wordpressdb", "command": "show tables"},
        {"pwnbus": "pwnbuspass"},
        "mysql --skip-ssl -h 127.0.0.1 -P 1234 -u pwnbus -ppwnbuspass wordpressdb -e 'show tables'",
        id="MYSQLCheck",
    ),
    pytest.param(
        "NFSCheck",
        {"remotefilepath": "/adir/textfile.txt", "filecontents": "Sample contents"},
        {},
        P + "/nfs_check 127.0.0.1 /adir/textfile.txt 'Sample contents'",
        id="NFSCheck",
    ),
    pytest.param(
        "OpenVPNCheck",
        {
            "ca": "MIIDSzCCAjOgAwIBAgIUNf7YivHK0rWciIy1HsNNx/tGDt4wDQYJKoZIhvcNAQELBQAwFjEUMBIGA1UEAwwLRWFzeS1SU0EgQ0EwHhcNMTkwMjE1MDI0NzUyWhcNMjkwMjEyMDI0NzUyWjAWMRQwEgYDVQQDDAtFYXN5LVJTQSBDQTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKCNXjK+4bIikgmGoGZHWRmLoJRxPoBkuy2U1jkaADBrfg4b3CgLP/OV4PGv1SmCvvLMuvdwKjA9JnYgtbEWLYyOi/Kxssjm5nLpJbx6KBZOvRjVzoKO0ljNh5nAXDiOyR+2PBUgp7A3PImM4R05m5pi+jd8+WbrQ8nfNQ5o9bFX26WpvWHo7gTxT8u+e6nL25U6TUYrPuTbw2/PGylaOVlEZTFhDO1GgxUUuPAwAmloQSoAbSNTI6Ch2mE8c3/dyyf4E1m6x7ves2cV44KQv8wTkLi1vQlhILmsjyH5oxlZARFl/hWXo6EBodLKVtVu8lWfNO4Le3qBYOijGfZQEB0CAwEAAaOBkDCBjTAdBgNVHQ4EFgQUG7NBOgwKvoAHZpwodZ45wVhpuUIwUQYDVR0jBEowSIAUG7NBOgwKvoAHZpwodZ45wVhpuUKhGqQYMBYxFDASBgNVBAMMC0Vhc3ktUlNBIENBghQ1/tiK8crStZyIjLUew03H+0YO3jAMBgNVHRMEBTADAQH/MAsGA1UdDwQEAwIBBjANBgkqhkiG9w0BAQsFAAOCAQEAXvwmtRzcLhdtJoNlK8Cc+BxjK9mgURgh4qt8BMP28CMfKw36xXWgxsbi4g5v08ohn+GrBikPmicL5p/V5yo6cC63Q0uI04k2k+jlC8PRXheyhQjYwSF6Ua18gAyXInR1GZ7t5l2OOBP5MWLGJxpLE8Xp1yn7v0kyAMXA3hOICi1BdS844ZVWhwiasm+BE7lybdtf15sAdYGmAjrrKwtCOlJSJrzOZLThUUlgGlwK2PAdeyYTkoQGyY3cKTfmsujTzyLsHKvqk7RPbKelvSfx1XEf1lH34305N8VSJQVc2UhNlaTS6YWJOyYVHPUsAqq8fJF4aZRd87VnhtOev3rKaA=="
        },
        {"test": "test"},
        P
        + "/openvpn_check 127.0.0.1 1234 test test MIIDSzCCAjOgAwIBAgIUNf7YivHK0rWciIy1HsNNx/tGDt4wDQYJKoZIhvcNAQELBQAwFjEUMBIGA1UEAwwLRWFzeS1SU0EgQ0EwHhcNMTkwMjE1MDI0NzUyWhcNMjkwMjEyMDI0NzUyWjAWMRQwEgYDVQQDDAtFYXN5LVJTQSBDQTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKCNXjK+4bIikgmGoGZHWRmLoJRxPoBkuy2U1jkaADBrfg4b3CgLP/OV4PGv1SmCvvLMuvdwKjA9JnYgtbEWLYyOi/Kxssjm5nLpJbx6KBZOvRjVzoKO0ljNh5nAXDiOyR+2PBUgp7A3PImM4R05m5pi+jd8+WbrQ8nfNQ5o9bFX26WpvWHo7gTxT8u+e6nL25U6TUYrPuTbw2/PGylaOVlEZTFhDO1GgxUUuPAwAmloQSoAbSNTI6Ch2mE8c3/dyyf4E1m6x7ves2cV44KQv8wTkLi1vQlhILmsjyH5oxlZARFl/hWXo6EBodLKVtVu8lWfNO4Le3qBYOijGfZQEB0CAwEAAaOBkDCBjTAdBgNVHQ4EFgQUG7NBOgwKvoAHZpwodZ45wVhpuUIwUQYDVR0jBEowSIAUG7NBOgwKvoAHZpwodZ45wVhpuUKhGqQYMBYxFDASBgNVBAMMC0Vhc3ktUlNBIENBghQ1/tiK8crStZyIjLUew03H+0YO3jAMBgNVHRMEBTADAQH/MAsGA1UdDwQEAwIBBjANBgkqhkiG9w0BAQsFAAOCAQEAXvwmtRzcLhdtJoNlK8Cc+BxjK9mgURgh4qt8BMP28CMfKw36xXWgxsbi4g5v08ohn+GrBikPmicL5p/V5yo6cC63Q0uI04k2k+jlC8PRXheyhQjYwSF6Ua18gAyXInR1GZ7t5l2OOBP5MWLGJxpLE8Xp1yn7v0kyAMXA3hOICi1BdS844ZVWhwiasm+BE7lybdtf15sAdYGmAjrrKwtCOlJSJrzOZLThUUlgGlwK2PAdeyYTkoQGyY3cKTfmsujTzyLsHKvqk7RPbKelvSfx1XEf1lH34305N8VSJQVc2UhNlaTS6YWJOyYVHPUsAqq8fJF4aZRd87VnhtOev3rKaA==",
        id="OpenVPNCheck",
    ),
    pytest.param(
        "POP3Check",
        {"domain": "test.com"},
        {"testuser": "passtest"},
        "medusa -R 1 -h 127.0.0.1 -n 1234 -u testuser@test.com -p passtest -M pop3",
        id="POP3Check",
    ),
    pytest.param(
        "POP3SCheck",
        {"domain": "test.com"},
        {"testuser": "passtest"},
        "medusa -s -R 1 -h 127.0.0.1 -n 1234 -u testuser@test.com -p passtest -M pop3",
        id="POP3SCheck",
    ),
    pytest.param(
        "POSTGRESQLCheck",
        {"database": "testdb", "command": r"\d"},
        {"pwnbus": "pwnbuspass"},
        r"PGPASSWORD=pwnbuspass psql -h 127.0.0.1 -p 1234 -U pwnbus -c '\d' testdb",
        id="POSTGRESQLCheck",
    ),
    pytest.param(
        "RDPCheck",
        {},
        {"pwnbus": "pwnbuspass"},
        P + "/rdp_check pwnbus pwnbuspass 127.0.0.1 1234",
        id="RDPCheck",
    ),
    pytest.param(
        "SMBCheck",
        {"remote_name": "COMPUTERNAME", "share": "ScoringShare", "file": "flag.txt", "hash": "123456789"},
        {"pwnbus": "pwnbuspass"},
        P
        + "/smb_check --host 127.0.0.1 --port 1234 --user pwnbus --pass pwnbuspass --remote-name COMPUTERNAME --share ScoringShare --file flag.txt --hash 123456789",
        id="SMBCheck",
    ),
    pytest.param(
        "SMTPCheck",
        {
            "touser": "tousr@someone.com",
            "subject": "A scoring engine test subject!",
            "body": "Hello!, This is an email body",
        },
        {"testuser@emaildomain.com": "passtest"},
        P
        + "/smtp_check testuser@emaildomain.com passtest testuser@emaildomain.com tousr@someone.com 'A scoring engine test subject!' 'Hello!, This is an email body' 127.0.0.1 1234",
        id="SMTPCheck",
    ),
    pytest.param(
        "SMTPSCheck",
        {
            "touser": "tousr@someone.com",
            "subject": "A scoring engine test subject!",
            "body": "Hello!, This is an email body",
        },
        {"testuser@emaildomain.com": "passtest"},
        P
        + "/smtps_check testuser@emaildomain.com passtest testuser@emaildomain.com tousr@someone.com 'A scoring engine test subject!' 'Hello!, This is an email body' 127.0.0.1 1234",
        id="SMTPSCheck",
    ),
    pytest.param(
        "SSHCheck",
        {"commands": "ls -l;id"},
        {"pwnbus": "pwnbuspass"},
        P + "/ssh_check 127.0.0.1 1234 pwnbus pwnbuspass 'ls -l;id'",
        id="SSHCheck",
    ),
    pytest.param(
        "TelnetCheck",
        {"timeout": 15, "commands": "ls -l;id"},
        {"pwnbus": "pwnbuspass"},
        P + "/telnet_check 127.0.0.1 1234 15 pwnbus pwnbuspass 'ls -l;id'",
        id="TelnetCheck",
    ),
    pytest.param(
        "VNCCheck",
        {},
        {"BLANK": "passtest"},
        "medusa -R 1 -h 127.0.0.1 -n 1234 -u '' '' -p passtest -M vnc",
        id="VNCCheck",
    ),
    pytest.param(
        "WebappNginxdefaultpageCheck",
        {"scheme": "http", "basepath": "/"},
        {},
        f"pytest --tb=line -s -q -rA --scheme=http --hostip=127.0.0.1 --hostport=1234 --basepath=/ {P}/webapp_nginxdefaultpage_check.py",
        id="WebappNginxdefaultpageCheck",
    ),
    pytest.param(
        "WebappScoringengineCheck",
        {"scheme": "https", "basepath": "/"},
        {"testuser": "testpass"},
        f"pytest --tb=line -s -q -rA --scheme=https --hostip=127.0.0.1 --hostport=1234 --basepath=/ --username=testuser --password=testpass {P}/webapp_scoringengine_check.py",
        id="WebappScoringengineCheck",
    ),
    pytest.param(
        "WinRMCheck",
        {"commands": "dir"},
        {"pwnbus": "pwnbuspass"},
        P + "/winrm_check 127.0.0.1 pwnbus pwnbuspass dir",
        id="WinRMCheck",
    ),
    pytest.param(
        "WordpressCheck",
        {"useragent": "testagent", "vhost": "www.example.com", "uri": "/wp-login.php"},
        {"admin": "password"},
        "curl -s -S -4 -v -L --cookie-jar - --header 'Host: www.example.com' -A 'testagent' --data 'log=admin&pwd=password' '127.0.0.1:1234/wp-login.php'",
        id="WordpressCheck",
    ),
]


@pytest.mark.parametrize("check_name,properties,accounts,expected_cmd", CHECK_PARAMS)
def test_check_command(check_name, properties, accounts, expected_cmd, db_session):
    """Verify that each check generates the expected shell command."""
    engine = Engine()
    service = Service(name="Example Service", check_name=check_name, host="127.0.0.1", port=1234)
    environment = Environment(service=service, matching_content="*")
    for prop_name, prop_value in properties.items():
        db.session.add(Property(environment=environment, name=prop_name, value=prop_value))
    for acct_name, acct_pass in accounts.items():
        db.session.add(Account(username=acct_name, password=acct_pass, service=service))
    db.session.add(service)
    db.session.add(environment)
    db.session.commit()

    check_obj = engine.check_name_to_obj(check_name)(environment)
    assert check_obj.command() == expected_cmd
