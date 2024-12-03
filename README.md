# octue/publish-strand-version GitHub action
A GitHub action that publishes updates to your JSON schema to the Octue Strands app, deducing its new semantic version.

## Usage
An example workflow that, on push to the `main` branch:
- Checks if your schema has changed
- If it has, asks the Strands app to deduce the new semantic version
- Publishes the new schema version on the Strands app as a new strand version

You can also specify the version using the `version` input.

```yaml
name: publish-strand-version

on:
  push:
    paths:
      - relative/path/to/schema.json
    branches:
      - main

jobs:
  publish-strand-version:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Publish strand version
        id: publish-strand-version
        uses: octue/publish-strand-version@0.1.0
        with:
          token: ${{ secrets.STRANDS_TOKEN }}
          account: your-account-handle
          name: your-strand
          path: relative/path/to/schema.json
          notes: Some notes.
          # version: 1.3.2  (optionally manually specify a version)

      - name: Print outputs
        run: |
          echo "Strand URL: ${{ steps.publish-strand-version.outputs.strand_url }}"
          echo "Strand version URI: ${{ steps.publish-strand-version.outputs.strand_version_uri }}"
          echo "Strand version UUID: ${{ steps.publish-strand-version.outputs.strand_version_uuid }}"
```
