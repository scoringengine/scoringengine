Webapp (Playwright)
^^^^^^^^^^^^^^^^^^^
Drives a real Chromium browser with Playwright to verify a web application works end to end. Use ``PASSED`` as the matching content.

- ``WebappNginxdefaultpageCheck``: loads the page and checks for the nginx default welcome header. `Does not use accounts`.
- ``WebappScoringengineCheck``: signs in to a Scoring Engine instance through its login form and checks it lands on the Services page. `Uses Accounts`.

Custom Properties:

.. list-table::
   :widths: 25 50

   * - scheme
     - http or https
   * - basepath
     - path the application is served under, with trailing slash (Ex: /)
