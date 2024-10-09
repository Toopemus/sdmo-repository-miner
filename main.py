import subprocess
import os
import urlparser
import docker
from repository import Repository

def mine_repo(directory:str):
    '''
    Get commit hashes here if needed
    os.chdir(directory) #Change directory to git repository. Remove if not needed
    p = subprocess.Popen(
        ["git", "log"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    #print(p.stdout.read())
    os.chdir("..") #Remove if initial cd wasn't needed
    '''

    #Do mining here
    client = docker.from_env()
    dir_real_path = os.path.realpath(directory)
    miner = client.containers.run(
        "tsantalis/refactoringminer", "-a " + "/repo",
        volumes={
            os.path.realpath(directory): {"bind": "/repo", "mode": "rw"}
        }
    )

    print(miner)


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
