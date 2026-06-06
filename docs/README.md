# Guide assets

This folder contains the editable practitioner guide, its PDF export, execution outputs, and original tutorial screenshots.

Important: the screenshots and diagrams in this repository are original tutorial illustrations generated from the included example implementation. They are not screenshots of Atlan, OpenMetadata, Alation, Protégé, TopBraid EDG, Stardog, GraphDB, or any other vendor product.

Before enabling catalog writes:

1. Review the dry-run OpenMetadata payloads against the API version deployed in your tenant.
2. Adapt the Atlan import CSV to your tenant import template or use the pyatlan SDK.
3. Add authentication, authorization, retries, audit logging, idempotency controls, and rollback behavior.
4. Publish only approved ontology releases.
