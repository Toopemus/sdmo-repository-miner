import csv

def list_project_urls(filename):
    print("Finding all unique projects...")
    with open(filename, newline='') as repositories:
        reader = csv.DictReader(repositories)
        projects = find_unique_projects(reader)
        print("There are", len(projects), "unique projects.")
        urls = map(to_url, projects)
        return urls

def find_unique_projects(csv):
    projects = set()
    for line in csv:
        projects.add(line["project"])
    return projects

def to_url(project):
    repo = project.split("_")
    if len(repo) == 2:
        return f"https://github.com/apache/{repo[1]}.git"
    else:
        return f"https://github.com/apache/{repo[0]}.git"
