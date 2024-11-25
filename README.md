# sdmo-repository-miner

Project work for the course Software Development, Maintenance, and Operations.

## Usage

1. Download `sonar_measures.csv` from the course instructions and place it in the project root.

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Pull the Docker image for RefactoringMiner:

```bash
docker pull tsantalis/refactoringminer
```
If you have RefactoringMiner installed you can skip this step.

4. create .env file and input your github token there

5. Run the script:

```bash
python main.py
```

Or if you wish to run RefactoringMiner from a local installation:
```bash
python main.py /path/to/rminer/RefactoringMiner
```

