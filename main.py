import csv

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

def main():
    print('Finding all unique projects...')
    with open('./sonar_measures.csv', newline='') as repositories:
        reader = csv.DictReader(repositories)
        projects = find_unique_projects(reader)
        print("There are", len(projects), "unique projects")
    for project in projects:
        print(to_url(project))

if __name__ == "__main__":
    main()
