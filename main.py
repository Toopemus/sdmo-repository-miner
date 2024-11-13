import subprocess
import os
import urlparser
import docker
import tarfile
import json
import csv
import issues

from datetime import datetime, timedelta
from repository import Repository
from pydriller import Repository as PyDriller
from pydriller import Git, Commit


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
def get_loc(commit: Commit) -> int:
    loc = 0
    for file in commit.modified_files:
        _, ext = os.path.splitext(file.filename)
        if not is_programing_language(ext):
            continue
        loc += file.nloc if file.nloc is not None else 0
    return loc

#GET HASHES
def get_hashes(repo_path: str):
    command = ["git", "-C", repo_path, "rev-list", "--all"]
    result = subprocess.run(command, stdout = subprocess.PIPE, text = True)
    return result.stdout.splitlines()

#ANALYSE THE REPOSITORY
def collect_developer_effort(repo_path: str, output_dir: str, refactoring_hashes: list[str]):
    refactoring_hashes = list(set(refactoring_hashes))  # Remove duplicates

    gr = Git(repo_path)
    processed_hashes = set()

    for commit_hash in refactoring_hashes:
            commit = gr.get_commit(commit_hash)
            developer_name = commit.author.name.replace(" ", "_") if commit.author else "Unknown"

            developer_file_name = f"{developer_name}_developer_effort.csv"
            output_file_path = os.path.join(output_dir, developer_file_name)

            with open(output_file_path, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)

                if os.path.getsize(output_file_path) == 0:
                    writer.writerow(["refactoring hash", "previous hash", "TLOC"])

                #for commit_hash in refactoring_hashes:
                if commit_hash not in processed_hashes:
                    # continue
                    processed_hashes.add(commit_hash)

                    if not commit.parents:
                        print(f"Skipping commit {commit_hash} (no parents found)")
                        continue
                    previous_commit_hash = commit.parents[0]
                    previous_commit = gr.get_commit(previous_commit_hash)

                    loc_current = get_loc(commit)
                    loc_previous = get_loc(previous_commit)
                    tloc = abs(loc_current - loc_previous)

                    writer.writerow([commit_hash, previous_commit_hash, tloc])
                    print(f"TLOC for {commit_hash} (compared to {previous_commit_hash}): {tloc}")


def mine_repo(repo_dir:str, output_dir:str):
    client = docker.from_env()
    dir_real_path = os.path.realpath(repo_dir)
    miner = client.containers.create("tsantalis/refactoringminer",
        "-a /repo -json " + MINER_OUTPUT_FILE,
        volumes={
            dir_real_path: {"bind": "/repo", "mode": "rw"}
        }
    )
    miner.start()
    miner.wait()
    bits, stat = miner.get_archive("diff/" + MINER_OUTPUT_FILE) # Get output file from exited container as a tarfile


    file = open(TAR_FILE, "wb") #Open file for writing output bits
    for chunk in bits:
        file.write(chunk)
    file.close()

    output_tar = tarfile.open(TAR_FILE, "r") #Extract json object from tarfile
    output_json = output_tar.extractfile(MINER_OUTPUT_FILE).read()
    output_tar.close()
    json_obj = json.loads(output_json)

    with open(os.path.join(output_dir, "rminer-output.json"), "w") as rminer_file:
        json.dump(json_obj, rminer_file)

    #Count different commit types to a directory. Also calculate time between commits average
    refactorings = {}
    previous_refactor_date = None
    refactor_date_difference_sum = timedelta()
    refactor_count = 0
    refactoring_hashes = []

    for commit in json_obj["commits"]:
        if len(commit["refactorings"]) > 0:
            commit_hash = commit["sha1"]
            refactoring_hashes.append(commit_hash)

        for refactoring in commit["refactorings"]:
            commit_date = get_commit_date(repo_dir, commit_hash)
            if previous_refactor_date:
                #First commit in list is the latest commit, do substraction accordingly
                refactor_date_difference_sum += previous_refactor_date - commit_date

            previous_refactor_date = commit_date
            refactor_count += 1
            type = refactoring["type"]
            refactorings[type] = refactorings.get(type, 0) + 1 #Increment count for refactoring type

    time_between_refactors = 0
    if len(refactorings) > 0: #Print output for now, get prettier output in the future
        time_between_refactors = refactor_date_difference_sum / refactor_count

    with open(os.path.join(output_dir, "refactorings.json"), "w") as refactorings_file:
        output = {
            "refactorings": refactorings,
            "average_time_between_refactors": str(time_between_refactors)
        }
        json.dump(output, refactorings_file)

    diffs = collect_diffs(dir_real_path, refactoring_hashes)
    with open(os.path.join(output_dir, "diffs.json"), "w") as diffs_file:
        json.dump(diffs, diffs_file)

    collect_developer_effort(repo_dir, output_dir, refactoring_hashes)

    os.remove(TAR_FILE)


def collect_diffs(path, hashes):
    print("Calculating diffs...")
    out = []
    for commit in PyDriller(path, only_commits=hashes).traverse_commits():
        diff_output = {
            "commit_hash": commit.hash,
            "diffs": []
        }
        for file in commit.modified_files:
            diff_output["diffs"].append({
                "file": file.new_path,
                "added": file.added_lines,
                "deleted": file.deleted_lines,
                "diff": file.diff
            })
        out.append(diff_output)
    print("Diffs collected.")
    return out


def get_commit_date(git_dir: str, hash: str) -> datetime:
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
           with Repository(url) as (dir_name, repo_name):
                current_dir = os.path.dirname(__file__)
                output_dir = os.path.join(current_dir, "output", repo_name)

                print(f"OUTPUT DIRECTORY: {output_dir}")
                os.makedirs(output_dir)

                mine_repo(dir_name, output_dir)
                issues.mine_issue_data(url, output_dir)
        except Exception as e:
            print(e)
        input("Mined a repository, newline to continue") #Input to reduce spam, remove when not needed

if __name__ == "__main__":
    main()
