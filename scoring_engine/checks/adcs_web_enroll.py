from scoring_engine.engine.basic_check import BasicCheck


class ADCSWebEnrollCheck(BasicCheck):
    """Verify an AD CS Enterprise CA issues a certificate via Web Enrollment.

    Uses certipy to request a certificate for the scoring account from a
    standard template (e.g. ``User``) through ``/certsrv``. This exercises IIS,
    the CertSrv app, AD authentication and the CA actually issuing, so it fails
    on a real CA outage but not when Blue hardens the ESC misconfigurations.

    Account usernames must be ``user@domain``. The service host is used as the
    target and DC address, so this assumes the CA runs on a domain controller.
    Optional: the worker image only includes certipy when built with
    ``INSTALL_CERTIPY=true``; otherwise the check fails with a message saying so.
    Requested certificates and keys are written to a temporary directory that
    is deleted after each run. Success prints "Got certificate".
    """

    required_properties = ["ca", "template"]
    CMD = (
        "if ! command -v certipy >/dev/null 2>&1; then "
        'echo "certipy is not installed in the worker image; rebuild it with INSTALL_CERTIPY=true"; '
        'else d=$(mktemp -d) && cd "$d" && '
        "certipy req -u {0} -p {1} -target {2} -target-ip {2} -dc-ip {2} -ca {3} -template {4} "
        "-web -http-scheme http -no-channel-binding 2>&1; "
        'cd / && rm -rf "$d"; fi'
    )

    def command_format(self, properties):
        account = self.get_random_account()
        return (account.username, account.password, self.host, properties["ca"], properties["template"])
