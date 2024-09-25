import csv
import subprocess
import os
import urlparser
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

def main():
    urls = urlparser.list_project_urls("./sonar_measures.csv")
    for url in urls:
        try:
            with Repository(url) as dir_name:
                mine_repo(dir_name)
        except Exception as e:
            print(e)
        input("Mined a repository, newline to continue") #Input to reduce spam, remove when not needed

if __name__ == "__main__":
    main()
