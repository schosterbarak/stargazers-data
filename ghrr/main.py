import argparse
import csv
import os
import sys
from datetime import date, datetime
from collections import namedtuple
from time import sleep
from github3 import login
from github3.exceptions import ForbiddenError
from tqdm import tqdm

RATE_LIMIT_BACKOFF = 10
gh_user = os.getenv('GITHUB_USER')
gh_token = os.getenv('GITHUB_TOKEN')
warn = lambda msg: print(f'\033[93mError: {msg}\033[0m', file=sys.stderr)
die = lambda msg: warn(msg) or exit(1)

User = namedtuple('User', ['email', 'location', 'username', 'company', 'followers', 'repos', 'organizations'])


def get_user_data(gh, u):
    username = u.login
    gh_user = gh.user(username)
    company = gh_user.company
    followers = gh_user.followers_count
    repos = gh_user.public_repos_count
    if company:
        company = company.replace("@", "")
    organizationsIterator = gh_user.organizations()
    organizations = []
    for org in organizationsIterator:
        organizations.append(org.login)
    return User(gh_user.email, gh_user.location, username, company, followers, repos, organizations)


def validate_params():
    if not gh_user:
        die("Please add GITHUB_USER environment variable")
    if not gh_token:
        die("Please add GITHUB_TOKEN environment variable")


class DummyUpdater(object):
    def update(self, c):
        pass


class DummyProgress(object):
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return DummyUpdater()

    def __exit__(self, type, value, traceback):
        pass


def wait_rate_limit(e: ForbiddenError):
    if not e.message.startswith('API rate limit exceeded'):
        raise e
    reset_time = e.response.headers.get('X-RateLimit-Reset')
    sleep_until = datetime.fromtimestamp(int(reset_time))
    # add 3 seconds to compensate for clocks being clocks
    seconds_to_sleep = int((sleep_until - datetime.now()).total_seconds()) + 3
    sleep_until_pretty = sleep_until.strftime('%m/%d/%Y, %H:%M:%S')
    warn(f'Rate limited. sleeping until "{sleep_until_pretty}" due to rate limit...')
    sleep(seconds_to_sleep)


def iterate_users(gh, users_iterator, users_count, user_writer, user_interaction, processed_users, progress=True):
    total = users_count if users_count > 0 else None
    progress = tqdm(total=total, desc=f'Fetching {user_interaction} data',
                    unit='users') if progress else DummyProgress()
    with progress as progress_bar:
        for u in users_iterator:
            if u.login in processed_users:
                progress_bar.update(1)
                continue

            data_received = False
            while not data_received:
                try:
                    user = get_user_data(gh, u)
                    user_writer.writerow([
                        user.username,
                        user.company,
                        user.organizations,
                        user.email,
                        user.location,
                        user.followers,
                        user.repos,
                        user_interaction
                    ])
                    processed_users.add(u.login)
                    data_received = True
                    progress_bar.update(1)
                except ForbiddenError as e:
                    wait_rate_limit(e)
                    continue
                except Exception as ae:
                    warn(f'got an unexpected error: {ae}, will wait a bit and try again')
                    sleep(RATE_LIMIT_BACKOFF)


def retrieve_repo_data(repo_owner, repo_name, output_filepath=None):
    validate_params()
    gh = login(gh_user, token=gh_token)
    repo_succeeded = False
    progress = True

    stargazers = None
    stargazers_count = None
    contributors = None
    subscribers = None
    subscribers_count = None

    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    processed_users = set()

    if not output_filepath:
        today = date.today()
        formated_today = today.strftime("%Y-%m-%d")  # YY-MM-DD
        output_filepath = os.path.join(output_dir, f'ghusers_{repo_owner}_{repo_name}_{formated_today}.csv')

    if output_filepath == '-':
        output = sys.stdout
        progress = False
    # Check if the output file already exists
    elif os.path.exists(output_filepath):
        # Read existing file to get the list of already processed users
        with open(output_filepath, mode='r') as existing_file:
            reader = csv.reader(existing_file)
            next(reader)  # Skip header
            for row in reader:
                processed_users.add(row[0])  # Assuming username is the first column

        # Open the file in append mode
        output = open(output_filepath, mode='a')
    else:
        # Open the file in write mode if it doesn't exist
        output = open(output_filepath, mode='w')
        # Write header only if creating a new file
        user_writer = csv.writer(output)
        user_writer.writerow(
            ["username", "company", "organizations", "email", "location", "followers_count", "public_repos_count",
             "user_interaction"])

    while not repo_succeeded:
        try:
            gh_repository = gh.repository(repo_owner, repo_name)
            stargazers = gh_repository.stargazers()
            stargazers_count = gh_repository.stargazers_count
            contributors = gh_repository.contributors()
            subscribers = gh_repository.subscribers()
            subscribers_count = gh_repository.subscribers_count

            repo_succeeded = True
        except ForbiddenError as e:
            wait_rate_limit(e)
            continue
        except Exception as ae:
            warn(f'got an unexpected error: {ae}, will wait a bit and try again')
            sleep(RATE_LIMIT_BACKOFF)

    with output as out:
        user_writer = csv.writer(out)
        iterate_users(gh, stargazers, stargazers_count, user_writer, "stargazer", processed_users, progress=progress)
        iterate_users(gh, subscribers, subscribers_count, user_writer, "subscriber", processed_users, progress=progress)
        iterate_users(gh, contributors, -1, user_writer, "contributor", processed_users, progress=progress)

    return output_filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='stargazers crawler')
    parser.add_argument('-o', '--organization', action='store',
                        help='github organization', required=True)
    parser.add_argument('-r', '--repository', action='store',
                        help='github repository', required=True)
    parser.add_argument('-f', '--file', action='store',
                        help='output file path', required=False)

    args = parser.parse_args()

    if not args.repository and not args.organization:
        die("No argument given. Try ` --help` for further information")

    repository = args.repository
    org = args.organization
    output_file = args.file
    retrieve_repo_data(org, repository, output_file)
