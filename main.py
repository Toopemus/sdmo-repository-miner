import csv

def find_unique_projects(csv):
    projects = set()
    for line in csv:
        projects.add(line["project"])
    return projects

def main():
    print('Finding all unique projects...')
    with open('./sonar_measures.csv', newline='') as repositories:
        reader = csv.DictReader(repositories)
        projects = find_unique_projects(reader)
        print("There are", len(projects), "unique projects")

if __name__ == "__main__":
    main()
