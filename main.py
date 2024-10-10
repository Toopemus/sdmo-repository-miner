import subprocess
import os
import urlparser
import docker
import tarfile
import json
from repository import Repository

TAR_FILE = "./temp.tar"
MINER_OUTPUT_FILE = "output.json"

def mine_repo(directory:str):
    print("mining...")
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
    
    output_tar = tarfile.open(TAR_FILE, "r")
    output_json = output_tar.extractfile(MINER_OUTPUT_FILE).read()
    json_obj = json.loads(output_json)

    #Count different commit types to a directory
    refactorings = {}
    for commit in json_obj["commits"]:
        for refactoring in commit["refactorings"]:
            type = refactoring["type"]
            refactorings[type] = refactorings.get(type, 0) + 1
        
    print(refactorings)
    
    p = subprocess.Popen(["rm", TAR_FILE])
    p.wait(5)



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
