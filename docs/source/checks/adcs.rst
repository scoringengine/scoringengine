AD CS Web Enrollment
^^^^^^^^^^^^^^^^^^^^
Requests a certificate from an AD CS Enterprise CA through Web Enrollment (``/certsrv``) using certipy. Use ``Got certificate`` as the matching content.

`Uses Accounts` (usernames must be ``user@domain``). The service host is used as the target and DC address, so the CA must run on a domain controller.

**Optional:** certipy is not in the default worker image. Set ``INSTALL_CERTIPY=true`` in ``.env`` and rebuild the worker (``docker compose build worker``) before using this check. For airgapped deployments, set it before running ``bin/create-airgapped-package.sh``.

Custom Properties:

.. list-table::
   :widths: 25 50

   * - ca
     - CA name (e.g. ``corp-DC01-CA``)
   * - template
     - a standard template the account may enroll in (e.g. ``User``)
