import subprocess
import shutil
import os
import stat
import re

class Repository(object):
    """
    Context manager class for git Repositories
    Handles cloning and removing the directories
    """
    def __init__(self, url):
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
            raise Exception("Problem while cloning repository from URL: " + url)

        repo_name = re.search("Cloning into '(.*)'", clone_output).group(1)
        current_dir = os.path.dirname(__file__)

        self.repo_name = repo_name
        self.directory_name = os.path.join(current_dir, repo_name)

    def __enter__(self):
        return (self.directory_name, self.repo_name)

    def __exit__(self, type, value, traceback):
        def remove_manually(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)

        shutil.rmtree(self.directory_name, onexc=remove_manually)

