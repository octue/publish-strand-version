> [!WARNING]
> This repository is currently in beta. Please use in production with caution.

# octue/publish-strand-version (GitHub Action)
A GitHub Action that publishes updates to your JSON schema to the Octue [Strands](https://strands.octue.com) app,
deducing its new semantic version.

## Usage
Below is an example workflow that, on push to the `main` branch:
- Checks if your schema has changed
- If it has, asks Strands to deduce the new semantic version
- Publishes the new schema version to Strands as a new strand version

You can also specify the version manually using the `version` input.

```yaml
name: example-workflow

on:
  push:
    paths:
      # This path is relative to the repository root.
      - relative/path/to/schema.json
    branches:
      - main

jobs:
  publish-my-schema-updates:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Publish strand version
        id: publish
        uses: octue/publish-strand-version@0.1.0-beta.0
        with:
          # See below for instructions on getting a token.
          token: ${{ secrets.STRANDS_TOKEN }}
          account: your-account-handle
          name: your-strand
          # This is the same path as the `paths` argument further up.
          path: relative/path/to/schema.json
          notes: Some notes.
          # version: 1.3.2   # Optionally, manually specify a version.

      - name: Print outputs
        run: |
          echo "Strand URL: ${{ steps.publish.outputs.strand_url }}"
          echo "Strand version URL: ${{ steps.publish.outputs.strand_version_url }}"
          echo "Strand version UUID: ${{ steps.publish.outputs.strand_version_uuid }}"
```

See a working example [here](.github/workflows/test-publish-strand-version.yml).

## Prerequisites
Before using this action, you must have:
- A [Strands](https://strands.octue.com) account
- Created a strand
- Created a strand access token and added it to the GitHub Actions secrets (see below)

### Creating a strand access token
1. Log in to your Strands account
2. Go to `https://strands.octue.com/<your-handle>/<your-strand>/integrations`
4. Click "Create an access token" and copy the token
5. Add the access token as a GitHub Actions repository secret:
   - Go to `https://github.com/<your-org>/<your-repository>/settings/secrets/actions`
   - Click "New repository secret"
   - Paste the token and give the secret a name (like `STRANDS_TOKEN` above)
   - Click "Add secret"

### More about access tokens
- They expire after one year
- They're specific to the strand you choose - an access token for strand A won't work for strand B
- You'll only see the token value once, so make sure to store it securely in a password manager if you need to use it again
- You can revoke an access token at any time by deleting it in your Strands user settings
