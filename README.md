> [!WARNING]
> This repository is currently in beta. Please use in production with caution.

# octue/publish-strand-version (GitHub Action)
A GitHub Action that publishes updates to JSON schemas defined in GitHub repositories to the Octue
[Strands](https://strands.octue.com) app.

## Usage
The action will:
- Check if the schema has changed
- If it has, ask [Strands](https://strands.octue.com) to suggest the new semantic version
- Publish the updated schema to Strands

You can also:
- Specify the version yourself manually or with your own code
- Use suggest-only mode (this gets the suggested semantic version but doesn't publish to
  [Strands](https://strands.octue.com))
- Add release notes to the schema (markdown optional but supported!)
- Disallow beta versioning (i.e. disallow versions < 1.0.0)

### Example workflow

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
  publish-updated-schema:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Publish strand version
        uses: octue/publish-strand-version@0.2.0
        with:
          # See below for instructions on getting a token.
          token: ${{ secrets.STRANDS_TOKEN }}
          account: your-account-handle
          name: your-strand
          # This is the same path as the `paths` argument further up.
          path: relative/path/to/schema.json
          ### Optional arguments ###
          # notes: Some notes    # Add some release notes
          # version: 1.3.2       # Manually specify a version
          # allow_beta: true     # Allow/disallow beta versioning (versions < 1.0.0)
          # suggest_only: false  # Choose whether to publish or just suggest the new version number
```

See our test workflow [here](.github/workflows/test-publish-strand-version.yml).

### Outputs
The available outputs from the action are:
- `strand_url`
- `strand_version_url`
- `strand_version_uuid`
- `suggested_version`

## Prerequisites
Before using this action, you must have:
- A [Strands](https://strands.octue.com) account
- Created a strand
- Created an access token for the strand and added it to your repository's GitHub Actions secrets (see below)

### Creating a strand token
1. Log in to your Strands account
2. Go to `https://strands.octue.com/<your-handle>/<your-strand>/settings`
4. Click "Create token" and copy the token
5. Add the token as a GitHub Actions repository secret:
   - Go to `https://github.com/<your-handle>/<your-repository>/settings/secrets/actions`
   - Click "New repository secret"
   - Paste the token and give the secret a name (like `STRANDS_TOKEN` above)
   - Click "Add secret"

### More about access tokens
- They expire after one year
- They're specific to the strand you choose - an access token for strand A won't work for strand B
- You'll only see the token value once, so make sure to store it securely in a password manager if you need to see it
  again
- You can revoke an access token at any time on the strand's settings page
