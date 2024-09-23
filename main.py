import csv
import subprocess
import re
import os

def mine_repo(directory:str):
    os.chdir(directory) #Change directory to git repository. Remove if not needed

    #Do mining here

    os.chdir("..") #Remove if initial cd wasn't needed


def clone_mine_and_delete(url: str):
    """
    Clone a repo, mine for refactoring efforts and remove the commit
    """

    #Clone repo
    clone_output = ""
    p = subprocess.Popen(
        ["git", "clone", url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

    for line in iter(p.stdout.readline, ""):
        print(line)
        clone_output += line
    p.stdout.close()
    exit_code = p.wait()

    if int(exit_code) != 0:
        print("Problem while cloning: " + url)

        return False
    directory_name = re.search("Cloning into '(.*)'", clone_output).group(1)

    mine_repo(directory_name)

    #Remove repo
    p = subprocess.Popen(["rm", "-rf", directory_name])
    p.wait(5)

    return True
    
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
        clone_mine_and_delete(to_url(project))
        input("Mined a repository, newline to continue") #Input to reduce spam, remove when not needed

if __name__ == "__main__":
    main()
