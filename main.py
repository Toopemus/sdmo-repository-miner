import subprocess
import os
import urlparser
import docker
import tarfile
import json
from datetime import datetime, timedelta
from repository import Repository

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
    bits, stat = miner.get_archive("diff/" + MINER_OUTPUT_FILE) #Get output file from exited container as a tarfile

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
    for commit in json_obj["commits"]:
        for refactoring in commit["refactorings"]:
            commit_hash = commit["sha1"]

            commit_date = get_commit_date(directory, commit_hash)
            if (previous_refactor_date):
                #First commit in list is the latest commit, do substraction accordingly
                refactor_date_difference_sum += previous_refactor_date - commit_date

            previous_refactor_date = commit_date
            refactor_count += 1

            type = refactoring["type"]
            refactorings[type] = refactorings.get(type, 0) + 1 #Increment count for refactoring type

    if len(refactorings) > 0: #Print output for now, get prettier output in the future
        print("Refactor types for " + directory)
        print(refactorings)
        print("Average time between refactors: ",  refactor_date_difference_sum/refactor_count)
    else:
        print("No refactorings for repository " + directory)

    p = subprocess.Popen(["rm", TAR_FILE]) #Remove tarfile
    p.wait(5)

def get_commit_date(git_dir:str, hash:str) -> datetime:
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
