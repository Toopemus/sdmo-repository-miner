import csv
import subprocess
import re
import os
from repository import Repository

def mine_repo(directory:str):
    os.chdir(directory) #Change directory to git repository. Remove if not needed

    #Do mining here
    #Print commit history for now
    p = subprocess.Popen(
        ["git", "log"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    print(p.stdout.read())

    os.chdir("..") #Remove if initial cd wasn't needed
    
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
        with Repository(to_url(project)) as dir_name:
            mine_repo(dir_name)
        input("Mined a repository, newline to continue") #Input to reduce spam, remove when not needed

if __name__ == "__main__":
    main()
