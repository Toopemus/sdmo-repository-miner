import subprocess
import os
import urlparser
import docker
import tarfile
import json
import csv
from datetime import datetime, timedelta
from repository import Repository
from pydriller import Repository as PyDriller


TAR_FILE = "./temp.tar"
MINER_OUTPUT_FILE = "output.json"
TIOBE_LANGUAGES = [
    "Python", "Java", "C", "C++", "C#", "JavaScript", "PHP", "Ruby", "Go",
    "TypeScript", "Swift", "Kotlin", "Rust", "Scala", "Dart", "R", "Objective-C"
]

#CHECK PROGRAMMING LANGUAGE
def is_programing_language(extension: str) -> bool:
    language_map = {
        ".py": "Python", ".java": "Java", ".c": "C", ".cpp": "C++", ".cs": "C#",
        ".js": "JavaScript", ".php": "PHP", ".rb": "Ruby", ".go": "Go",
        ".ts": "TypeScript", ".swift": "Swift", ".kt": "Kotlin", ".rs": "Rust",
        ".scala": "Scala", ".dart": "Dart", ".r": "R", ".m": "Objective-C"
    }
    return language_map.get(extension) in TIOBE_LANGUAGES

#GET LINES OF CODE
def get_loc(directory: str) -> int:
    loc = 0
    for root, _, files in os.walk(directory):
        for filename in files:
            _, ext = os.path.splitext(filename)
            if is_programing_language(ext):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', errors='ignore') as f:
                    loc += sum(1 for line in f if line.strip())
    return loc

#GET HASHES
def get_hashes(repo_path: str):
    command = ["git", "-C", repo_path, "rev-list", "--all"]
    result = subprocess.run(command, stdout = subprocess.PIPE, text = True)
    return result.stdout.splitlines()

#ANALYSE THE REPOSITORY
def analyze_repo(repo_path: str, output_csv: str):
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["refactoring hash", "previous hash", "TLOC"])

        commit_hashes = get_hashes(repo_path)

        previous_commit_hash = None
        previous_loc = None

        #traversing each commit hash and calculate
        for commit_hash in commit_hashes:
            
            subprocess.run(["git", "-C", repo_path, "checkout", commit_hash], check = True)

            loc_current = get_loc(repo_path)

            if previous_commit_hash and previous_loc is not None:
                tloc = abs(loc_current - previous_loc)
                #write changes to CSV
                writer.writerow([commit_hash, previous_commit_hash, tloc])
                print(f"TLOC for {commit_hash} (compared to {previous_commit_hash}): {tloc}")

                previous_commit_hash = commit_hash
                previous_loc = loc_current

        subprocess.run(["git", "-C", repo_path, "checkout", "main"], check = True)

def mine_repo(directory:str):
    print("1")
    client = docker.from_env()
    print("2")
    dir_real_path = os.path.realpath(directory)
    print("3")
    miner = client.containers.create("tsantalis/refactoringminer",
        "-a /repo -json " + MINER_OUTPUT_FILE,
        volumes={
            dir_real_path: {"bind": "/repo", "mode": "rw"}
        }
    )
    miner.start()
    print("4")
    miner.wait()
    bits, stat = miner.get_archive("diff/" + MINER_OUTPUT_FILE) #Get output file from exited container as a tarfile

    file = open(TAR_FILE, "wb") #Open file for writing output bits
    print("5")
    for chunk in bits:
        file.write(chunk)
    print("6")
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
            if (previous_refactor_date):
                #First commit in list is the latest commit, do substraction accordingly
                refactor_date_difference_sum += previous_refactor_date - commit_date

            previous_refactor_date = commit_date
            refactor_count += 1

            type = refactoring["type"]
            refactorings[type] = refactorings.get(type, 0) + 1 #Increment count for refactoring type

    # TODO: save to file
    diffs = collect_diffs(dir_real_path, refactoring_hashes)

    if len(refactorings) > 0: #Print output for now, get prettier output in the future
        print("Refactor types for " + directory)
        print(refactorings)
        print("Average time between refactors: ",  refactor_date_difference_sum/refactor_count)
    else:
        print("No refactorings for repository " + directory)

    p = subprocess.Popen(["rm", TAR_FILE]) #Remove tarfile
    #print(TAR_FILE)
    #p = os.remove(TAR_FILE)
    p.wait(5)

def collect_diffs(path, hashes):
    print("Calculating diffs...")

    out = []
    for commit in PyDriller(path, only_commits=hashes).traverse_commits():
        diff_output = {}
        for file in commit.modified_files:
            diff_output["sha1"] = commit.hash
            diff_output["added"] = file.added_lines
            diff_output["deleted"] = file.deleted_lines
            diff_output["diff"] = file.diff
        out.append(diff_output)

    print("Diffs collected.")

    return out

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
    output_csv = "developer_effort.csv"
    for url in urls:
        try:
           with Repository(url) as dir_name:
                #dir_name = mine_repo(url)
                analyze_repo(mine_repo(dir_name), output_csv)
        except Exception as e:
            print(e)
        input("Mined a repository, newline to continue") #Input to reduce spam, remove when not needed

if __name__ == "__main__":
    main()
