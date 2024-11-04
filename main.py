import subprocess
import os
import urlparser
import docker
import tarfile
import json
import requests
from datetime import datetime, timedelta
from repository import Repository
#from pydriller import Repository as PyDriller

GITHUB_API_URL = "https://api.github.com/repos/"
APACHE_JIRA_API_URL = "https://issues.apache.org/jira/rest/api/2"
TAR_FILE = "./temp.tar"
MINER_OUTPUT_FILE = "output.json"

def mine_repo(directory:str):
    client = docker.from_env()
    dir_real_path = os.path.realpath(directory)
    miner = client.containers.create("tsantalis/refactoringminer",
        "-a /repo -json " + MINER_OUTPUT_FILE,
        volumes={
            dir_real_path: {"bind": "/repo", "mode": "rw"}
        }
    )
    miner.start()
    miner.wait()
    bits, stat = miner.get_archive("diff/" + MINER_OUTPUT_FILE) # Get output file from exited container as a tarfile


    file = open(TAR_FILE, "wb") #Open file for writing output bits
    for chunk in bits:
        file.write(chunk)
    file.close()

    output_tar = tarfile.open(TAR_FILE, "r") #Extract json object from tarfile
    output_json = output_tar.extractfile(MINER_OUTPUT_FILE).read()
    output_tar.close()
    json_obj = json.loads(output_json)

    #Count different commit types to a directory. Also calculate time between commits average
    refactorings = {}
    previous_refactor_date = None
    refactor_date_difference_sum = timedelta()
    refactor_count = 0
    refactoring_hashes = []

    for commit in json_obj["commits"]:
        for refactoring in commit["refactorings"]:
            commit_hash = commit["sha1"]
            refactoring_hashes.append(commit_hash)

            commit_date = get_commit_date(directory, commit_hash)
            if previous_refactor_date:
                #First commit in list is the latest commit, do substraction accordingly
                refactor_date_difference_sum += previous_refactor_date - commit_date

            previous_refactor_date = commit_date
            refactor_count += 1
            type = refactoring["type"]
            refactorings[type] = refactorings.get(type, 0) + 1 #Increment count for refactoring type

    # TODO: save to file
    #diffs = collect_diffs(dir_real_path, refactoring_hashes)

    if len(refactorings) > 0: #Print output for now, get prettier output in the future
        print("Refactor types for " + directory)
        print(refactorings)
        print("Average time between refactors:", refactor_date_difference_sum / refactor_count)
    else:
        print("No refactorings for repository " + directory)


    p = subprocess.Popen(["rm", TAR_FILE]) # Remove tarfile
    p.wait(5)


#def collect_diffs(path, hashes):
#    print("Calculating diffs...")
#    out = []
#    for commit in PyDriller(path, only_commits=hashes).traverse_commits():
#        diff_output = {"sha1": commit.hash}
#        for file in commit.modified_files:
#            diff_output.update({
#                "added": file.added_lines,
#                "deleted": file.deleted_lines,
#                "diff": file.diff
#            })
#        out.append(diff_output)
#    print("Diffs collected.")
#    return out


def get_commit_date(git_dir: str, hash: str) -> datetime:
    """
    Return date and time for a commit in a git directory
    """
    p = subprocess.Popen(
        ["git", "-C", git_dir, "show", "--no-patch", "--format=%ci", hash],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    return datetime.strptime(p.stdout.read().strip(), "%Y-%m-%d %H:%M:%S %z")

# Check if GitHub has issues enabled
def check_github_issues(owner, repo):
    response = requests.get(f"{GITHUB_API_URL}{owner}/{repo}")
    if response.status_code == 200:
        repo_data = response.json()
        return repo_data.get("has_issues", False)
    print(f"Failed to retrieve GitHub repo data: {response.status_code}")
    return False

# Get issues from GitHub
def fetch_github_issues(owner, repo):
    issues = []
    page = 1
    while True:
        response = requests.get(f"{GITHUB_API_URL}{owner}/{repo}/issues?page={page}")
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
    if project_key:
        response = requests.get(f"{APACHE_JIRA_API_URL}/search?jql=project={project_key}")
    else:
        response = requests.get(f"{APACHE_JIRA_API_URL}/project")

    if response.status_code == 200:
        return response.json()
    print(f"Failed to retrieve JIRA data: {response.status_code} - {response.text}")
    return None

# Find JIRA project key
def find_jira_project_key(url, jira_projects):
    for project in jira_projects:
        if project['name'].lower() in url.lower() or project['key'].lower() in url.lower():
            return project['key']
    return None


def parse_github_repo(url):
    parts = url.split('/')
    return parts[-2], parts[-1]


def main():
    urls = urlparser.list_project_urls("./sonar_measures.csv")
    jira_projects = fetch_jira_data()  # Fetch all JIRA projects from Apache JIRA

    for url in urls:
        try:
            if "github.com" in url:
                # GitHub repository processing
                owner, repo = parse_github_repo(url)
                with Repository(url) as dir_name:
                    if check_github_issues(owner, repo):
                        issues = fetch_github_issues(owner, repo)
                        print(f"Retrieved {len(issues)} issues for GitHub repo {owner}/{repo}")
                        with open(f"{repo}_github_issues.json", "w") as issue_file:
                            json.dump(issues, issue_file, indent=4)
                    else:
                        print(f"Issues are not enabled for {owner}/{repo}")
                    mine_repo(dir_name)

            elif "issues.apache.org/jira" in url:
                # JIRA project processing
                project_key = find_jira_project_key(url, jira_projects)
                if project_key:
                    issues = fetch_jira_data(project_key=project_key).get("issues", [])
                    print(f"Retrieved {len(issues)} issues for JIRA project {project_key}")
                    with open(f"{project_key}_jira_issues.json", "w") as issue_file:
                        json.dump(issues, issue_file, indent=4)
                else:
                    print(f"No JIRA project found for URL: {url}")

            else:
                print(f"Unrecognized URL format for {url}. Skipping.")

        except Exception as e:
            print(f"Error processing {url}: {e}")
        input("Mined a repository, newline to continue") #Input to reduce spam, remove when not needed

if __name__ == "__main__":
    main()