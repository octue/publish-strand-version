# octue/publish-strand-version (GitHub Action)
A GitHub Action that publishes updates to JSON schemas defined in a GitHub repository to the Octue
[Strands](https://strands.octue.com) app. The action will:
- Check if the schema has changed
- If it has, get the new semantic version from [Strands](https://strands.octue.com)
- Publish the updated schema to [Strands](https://strands.octue.com)

You can also:
- Specify the version yourself manually or with your own code
- Use suggest-only mode (this gets the suggested semantic version but doesn't publish to
  [Strands](https://strands.octue.com))
- Add release notes to the schema (markdown optional but supported!)
- Disallow beta versioning (i.e. disallow versions < 1.0.0)

## Usage

## Examples
- [Publish an updated schema](#publish-an-updated-schema)
- [Publish with a specific semantic version](#publish-with-a-specific-semantic-version)
- [Get suggested semantic version](#get-suggested-semantic-version)

### Publish an updated schema

```yaml
on:
  push:
    paths:
      # Only trigger if the schema has changed.
      - relative/path/to/schema.json
    branches:
      - main

jobs:
  publish-updated-schema:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Get release notes
        id: notes
        run: echo "release_notes=$(cat tests/schema/notes.md)" >> $GITHUB_OUTPUT

      - name: Publish strand version
        uses: octue/publish-strand-version@0.2.0
        with:
          token: ${{ secrets.STRANDS_TOKEN }}
          account: your-account-handle
          name: your-strand
          path: relative/path/to/schema.json
          notes: ${{ steps.notes.outputs.release_notes }}
```

### Publish with a specific semantic version
```yaml
on:
  push:
    paths:
      # Only trigger if the schema has changed.
      - relative/path/to/schema.json
    branches:
      - main

jobs:
  publish-updated-schema:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Get release notes
        id: notes
        run: echo "release_notes=$(cat tests/schema/notes.md)" >> $GITHUB_OUTPUT

      - name: Get version
        id: version
        run: |
          <some code to get or choose the version> && \
          echo "version=$version" >> $GITHUB_OUTPUT

      - name: Publish strand version
        uses: octue/publish-strand-version@0.2.0
        with:
          token: ${{ secrets.STRANDS_TOKEN }}
          account: your-account-handle
          name: your-strand
          path: relative/path/to/schema.json
          notes: ${{ steps.notes.outputs.release_notes }}
          version: ${{ steps.version.outputs.version }}
```

### Get suggested semantic version
```yaml
on:
  push:
    paths:
      # Only trigger if the schema has changed.
      - relative/path/to/schema.json

jobs:
  get-suggested-version:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Suggest semantic version
        id: version
        uses: octue/publish-strand-version@0.2.0
        with:
          token: ${{ secrets.STRANDS_TOKEN }}
          account: your-account-handle
          name: your-strand
          path: relative/path/to/schema.json
          suggest_only: true

      - name: Print suggested version
        run: echo ${{ steps.version.outputs.suggested_version }}
```

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
