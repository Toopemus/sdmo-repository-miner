import requests
import json

GITHUB_API_URL = "https://api.github.com/repos/"
APACHE_JIRA_API_URL = "https://issues.apache.org/jira/rest/api/2"


def read_token():
    with open(".env", "r") as token_file:
        return token_file.read()

token = read_token()
headers = {
    'Authorization': f'token {token}'
}
    
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
            print(f"Failed to fetch issues from GitHub: {response.status_code}")
            break
        page_data = response.json()
        if not page_data:
            break
        issues.extend(page_data)
        page += 1
    return issues

# Get the JIRA data
def fetch_jira_data(project_key=None):
    """
    Gets the jira issues from repository.
    >>> issues = fetch_jira_data('GEOMETRY')
    >>> len(issues) != 0
    True
    """
    if project_key:
        response = requests.get(f"{APACHE_JIRA_API_URL}/search?jql=project={project_key}")
    else:
        response = requests.get(f"{APACHE_JIRA_API_URL}/project")

    if response.status_code == 200:
        return response.json()
    print(f"Failed to retrieve JIRA data: {response.status_code} - {response.text}")
    return None

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
    for project in jira_projects:
        if project['key'].lower() == repo.lower():
            return project['key']
        
    for project in jira_projects:
        if project['name'].lower() in repo.lower():
            return project['key']
    return None

def parse_github_repo(url):
    parts = url.split('/')
    return parts[-2], parts[-1]

def mine_issue_data(url):

    jira_projects = fetch_jira_data()  # Fetch all JIRA projects from Apache JIRA

    # GitHub repository processing
    owner, repo = parse_github_repo(url)
    if check_github_issues(owner, repo):
        issues = fetch_github_issues(owner, repo)
        print(f"Retrieved {len(issues)} issues for GitHub repo {owner}/{repo}")
        with open(f"{repo}_github_issues.json", "w") as issue_file:
            json.dump(issues, issue_file)
    elif find_jira_project_key(url,jira_projects):
        # JIRA project processing
        project_key = find_jira_project_key(url, jira_projects)
        if project_key:
            issues = fetch_jira_data(project_key=project_key).get("issues", [])
            print(f"Retrieved {len(issues)} issues for JIRA project {project_key}")
            with open(f"{project_key}_jira_issues.json", "w") as issue_file:
                json.dump(issues, issue_file)
        else:
            print(f"No JIRA project found for URL: {url}")
    else:
        print(f"Issues are not enabled for {owner}/{repo}")

if __name__ == "__main__":
    import doctest
    doctest.testmod()