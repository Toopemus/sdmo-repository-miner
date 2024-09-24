import subprocess
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


        self.directory_name = re.search("Cloning into '(.*)'", clone_output).group(1)

    def __enter__(self):
        return self.directory_name
    
    def __exit__(self, type, value, traceback):
        p = subprocess.Popen(["rm", "-rf", self.directory_name])
        p.wait(5)


