import os
import requests
import json
from main import current_time

GITHUB_API_URL = "https://api.github.com/repos/"
APACHE_JIRA_API_URL = "https://issues.apache.org/jira/rest/api/2"

def fetch_jira_projects():
    """
    List of all apache software foundations jira spaces
    """
    response = requests.get(f"{APACHE_JIRA_API_URL}/project")

    if response.status_code == 200:
        return response.json()

    print(f"{current_time()} - Failed to retrieve JIRA projects: {response.status_code} - {response.text}")
    return []

def read_token():
    with open(".env", "r") as token_file:
        return token_file.read()

token = read_token()
headers = {
    'Authorization': f'token {token.strip()}'
}
jira_projects = fetch_jira_projects()
jira_projects = sorted(jira_projects, key=lambda project: len(project["key"]))
jira_projects.reverse()

def check_github_issues(owner, repo):
    response = requests.get(f"{GITHUB_API_URL}{owner}/{repo}", headers = headers)
    return response.status_code == 200

# Get issues from GitHub
def fetch_github_issues(owner, repo):
    """
    Gets the github issues from repository.
    >>> issues = fetch_github_issues('apache', 'incubator-iotdb')
    >>> len(issues) != 0
    True
    """

    issues = []
    page = 1
    while True:
        response = requests.get(f"{GITHUB_API_URL}{owner}/{repo}/issues?page={page}", headers = headers)
        if response.status_code != 200:
            print(f"{current_time()} - Failed to fetch issues from GitHub: {response.status_code}")
            break
        page_data = response.json()
        if not page_data:
            break
        issues.extend(page_data)
        page += 1
    return issues

# Get the JIRA data
def fetch_jira_issues(project_key):
    """
    Gets the jira issues from repository.
    >>> issues = fetch_jira_data('GEOMETRY')
    >>> len(issues) != 0
    True
    """
    issues = []

    response = requests.get(f"{APACHE_JIRA_API_URL}/search?jql=project={project_key}&maxResults=100")
    body = response.json()
    total = body["total"]

    issues.extend(body["issues"])

    issues_start_index = 100
    while issues_start_index < total:
        print(f"Querying for issues {issues_start_index}-{issues_start_index + 100} out of {total}")
        response = requests.get(f"{APACHE_JIRA_API_URL}/search?jql=project={project_key}&startAt={issues_start_index}&maxResults=100")

        if response.status_code != 200:
            print(f"{current_time()} - Failed to retrieve JIRA data: {response.status_code} - {response.text}")

        body = response.json()

        issues.extend(body["issues"])

        issues_start_index += 100

    return issues

# Find JIRA project key
def find_jira_project_key(repo, jira_projects):
    """
    Get key for jira project.
    >>> find_jira_project_key('iotdb', fetch_jira_data())
    'IOTDB'
    >>> find_jira_project_key('abcdef', fetch_jira_data()) is None
    True
    >>> find_jira_project_key('sling-org-apache-sling-scripting-thymeleaf', fetch_jira_data())
    'SLING'
    """
    if repo.startswith("sling"):
        # All sling repositories have the same issue tracker
        return "SLING"
    if repo.startswith("incubator-"):
        # Remove 'incubator' from start to avoid false positives
        repo = repo[len("incubator-"):]

    # First search for exact matches
    for project in jira_projects:
        if project['key'].lower() == repo.lower():
            return project['key']

    # Then if there's no exact matches, we search for the key in the repo name
    for project in jira_projects:
        if project['key'].lower() in repo.lower():
            return project['key']
    return None

def parse_github_repo(url):
    parts = url.split('/')
    return parts[-2], parts[-1]

# We store project keys that have already been crawled through to avoid going
# through the same issues multiple times. This applies to projects like SLING,
# which has multiple repos but a single issue tracker.
already_fetched = []

def mine_issue_data(url, output_dir):
    # GitHub repository processing
    owner, repo = parse_github_repo(url)
    if check_github_issues(owner, repo):
        issues = fetch_github_issues(owner, repo)
        print(f"{current_time()} - Retrieved {len(issues)} issues for GitHub repo {owner}/{repo}")
        with open(os.path.join(output_dir, f"{repo}_github_issues.json"), "w") as issue_file:
            json.dump(issues, issue_file)
    elif find_jira_project_key(repo, jira_projects):
        # JIRA project processing
        project_key = find_jira_project_key(repo, jira_projects)
        if project_key and project_key not in already_fetched:
            issues = fetch_jira_issues(project_key)
            print(f"{current_time()} - Retrieved {len(issues)} issues for JIRA project {project_key}")
            with open(os.path.join(output_dir, f"{project_key}_jira_issues.json"), "w") as issue_file:
                json.dump(issues, issue_file)
            already_fetched.append(project_key)
        else:
            print(f"{current_time()} - JIRA issues already mined for: {url}")
    else:
        print(f"{current_time()} - Issues are not enabled for {owner}/{repo}")

if __name__ == "__main__":
    import doctest
    doctest.testmod()
