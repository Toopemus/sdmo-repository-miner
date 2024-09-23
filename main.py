import urlparser

def main():
    urls = urlparser.list_project_urls("./sonar_measures.csv")
    for url in urls:
        print(url)

if __name__ == "__main__":
    main()
