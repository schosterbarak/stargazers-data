# GitHub Research Runner (ghrr)
A utility to collect data from GitHub stargazers, subscribers and contributors of a selected project.

Use cases are detailed at the following blog: https://www.battery.com/blog/fantastic-developer-community-heroes-and-where-to-find-them/

## installing

```bash
git clone https://github.com/schosterbarak/ghrr.git
cd ghrr
pip install -r requirements.txt
```

## Using
1. Create GitHub personal access token using the following guide: https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token

2. Adding environment variables:
   ```bash
   export GITHUB_USER=XXX
   export GITHUB_TOKEN=YYY
   ```

3. Running the application:
   1. In the terminal:
      ```bash
      #an example command 
      ghrr -o bridgecrewio -r checkov 
      ```
   2. Streamlit app:
      ```bash
      streamlit run app.py
      ```
      The streamlit app will let you upload an existing CSV, or add a repo URL for retrieving a new repository's data.

## Results
### Terminal running
A CSV with the repo data will be created at the following format under an `outputs/` directory:
`ghusers_{ORG}_{REPO}_{DATE}.csv`

example:
`ghusers_bridgecrewio_checkov_2020-09-21.csv`

| username   | company  | organizations   | email           | location    | followers_count   | public_repos_count   | user_iteraction   |
| --------   | -------  | -------------   | -------         | --------    | ---------------   | ------------------   | ---------------   |
| Jon.       | ACME.    | ACME.           | jon@acme.com    | US          | 3                 | 200                  | stargazer         |
| Jane       | ACME.    | ACME.           | jane@acme.com   | IL          | 3                 | 200                  | collaborator      |


### Streamlit app
The CSV above will also be created, but a dashboard will be created with the following components:
1. Most followed users
2. Number of repositories per user
3. Number of users by location
4. Number of users by organization
5. A table of raw information

![GitHub Influencers Dashboard](/influencers%20dashboard.png "GitHub Influencers Dashboard").

