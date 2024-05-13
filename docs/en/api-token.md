# To get an access token for the Albert API

This document guides you through the steps to obtain and manage your access tokens for the Albert API.

### Step 1: Get a temporary token

Get started by obtaining a temporary token that will allow you to make initial requests. Replace `<your email address>` and `<your password>` with your credentials:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"email":"<votre adresse email>","password":"<votre mot de passe>"}' https://albert.etalab.gouv.fr/api/v2/sign_in
```

### Step 2: Save the token

Save the obtained token in an environment variable to make it easier to use in future requests:

```bash
export ALBERT_API_KEY=<le jeton obtenu>
```

### Step 3: Create an API token

Once the temporary token is saved, you can create a permanent API token with the following command. Replace `my_token_name` with a meaningful name for your token:

```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ALBERT_API_KEY" -d '{"name":"my_token_name"}' https://albert.etalab.gouv.fr/api/v2/user/token/new
```

### Step 4: List your tokens

To see all the tokens you have created, use this command:

```bash
curl -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $ALBERT_API_KEY" https://albert.etalab.gouv.fr/api/v2/user/token
```

### Step 5: Delete a token

To delete a specific token, replace `$ALBERT_API_TOKEN` with the token you want to delete:

```bash
curl -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer $ALBERT_API_KEY" https://albert.etalab.gouv.fr/api/v2/user/token/$ALBERT_API_TOKEN
```

*Be careful to secure your tokens and not share them with anyone.*
