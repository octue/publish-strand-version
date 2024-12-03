# octue/publish-strand-version (GitHub Action)
A GitHub Action that publishes updates to your JSON schema to the Octue [Strands](https://strands.octue.com) app,
deducing its new semantic version.

## Usage
Here's an example workflow that, on push to the `main` branch:
- Checks if your schema has changed
- If it has, asks Strands to deduce the new semantic version
- Publishes the new schema version to Strands as a new strand version

You can also specify the version using the `version` input.

```yaml
name: publish-strand-version

on:
  push:
    paths:
      - relative/path/to/schema.json  # This path is relative to the repository root.
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
          token: ${{ secrets.STRANDS_TOKEN }}  # See below for instructions on getting a token.
          account: your-account-handle
          name: your-strand
          path: relative/path/to/schema.json  # This is the same path as the `paths` argument further up.
          notes: Some notes.
          # version: 1.3.2   # Optionally, manually specify a version (or feed in a version calculated elsewhere in the workflow)

      - name: Print outputs
        run: |
          echo "Strand URL: ${{ steps.publish-strand-version.outputs.strand_url }}"
          echo "Strand version URI: ${{ steps.publish-strand-version.outputs.strand_version_uri }}"
          echo "Strand version UUID: ${{ steps.publish-strand-version.outputs.strand_version_uuid }}"
```

## Prerequisites
Before using this action, you must have:
- A [Strands](https://strands.octue.com) account
- Created a strand
- Created a strand access token and added it to the GitHub Actions secrets (see below)

### Creating a strand access token
1. Log in to your Strands account
2. Navigate to the strand you want to publish new versions to
3. Click on "Strand settings"
4. Click "Create an access token". Store your token securely in a password manager.
5. Add the access token to the GitHub Actions secrets for your repository as a repository secret
   - Go to `https://github.com/<your-org>/<your-repository>/settings/secrets/actions`
   - Click "New repository secret"
   - Paste the token and give the secret a name (like `STRANDS_TOKEN` above)
   - Click "Add secret"

### More about access tokens
- They expire after one year
- They're specific to the strand you choose - an access token for strand A won't work for strand B
- You'll only see the token value once, so make sure to record and store it securely
- You can revoke an access token at any time by deleting it in your Strands user settings
