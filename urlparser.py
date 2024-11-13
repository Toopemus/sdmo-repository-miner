import csv

def list_project_urls(filename):
    print("Finding all unique projects...")
    with open(filename, newline='') as repositories:
        reader = csv.DictReader(repositories)
        projects = find_unique_projects(reader)
        print("There are", len(projects), "unique projects.\n")
        urls = map(to_url, projects)
        return urls

def find_unique_projects(csv):
    projects = set()
    for line in csv:
        projects.add(line["project"])
    return projects

def to_url(project):
    """
    Parses a project name into a clonable GitHub URL under the Apache organization.

    >>> to_url('test-repository')
    'https://github.com/apache/test-repository.git'

    Also removes the organization name that is prepended to some of the names:
    >>> to_url('apache_test-repository')
    'https://github.com/apache/test-repository.git'

    >>> to_url('apache-test-repository')
    'https://github.com/apache/test-repository.git'
    """
    if project.startswith("apache_") or project.startswith("apache-"):
        project = project[len("apache_"):]

    return f"https://github.com/apache/{project}.git"

if __name__ == "__main__":
    import doctest
    doctest.testmod()
