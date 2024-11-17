import matplotlib.pyplot as plt
import os
import json
import re
from datetime import timedelta, datetime

OUTPUT_ROOT_DIR = "./output"
REFACTORING_FILE = "refactorings.json"
PROGRAM_LOG_FILE = "../program_backup.txt"
LINE_TIME_PREFIX_RE = "(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+) - "

LOG_REGEX_SEQUENCE = [
    r"Running RefactoringMiner...",
    r"Parsing output from RefactoringMiner...",
    r"Collecting diffs...",
    r"Collecting developer effort...",
    r"Mining issue data...",
    r"Success!",
]


def estimate_mining_time_division():
    """
    Go through log file line by line to estimate the time taken by each mining step
    and total mining time. Try to find a matching line for previously matched line.
    If a non matching line is found, return to sequence index zero and start over.
    """
    step_time_sum = [timedelta() for i in range(0, 5)] #Indices are diffrent steps in the mining process
    total_time = timedelta()

    with open(PROGRAM_LOG_FILE, "r") as log_file:
        log_sequence_index = 0
        time_for_step = None
        previous_time = None
        for line in log_file.readlines():
            if re_match := re.search(
                LINE_TIME_PREFIX_RE + LOG_REGEX_SEQUENCE[log_sequence_index], line
            ):
                action_time = datetime(1, 1, 1, int(re_match['hours']), int(re_match["minutes"]), int(re_match["seconds"]))
                if previous_time:
                    time_for_step = action_time - previous_time
                    if time_for_step < timedelta(): #Step happened over midnight
                        #Horrible way to do this but whatever. assume no step takes over 24 hours
                        action_time = action_time = datetime(1, 1, 2, int(re_match['hours']), int(re_match["minutes"]), int(re_match["seconds"]))
                        time_for_step = action_time - previous_time

                    total_time += time_for_step
                    step_time_sum[log_sequence_index - 1] += time_for_step
                
                if log_sequence_index == 5: #start over on success
                    log_sequence_index = 0
                    previous_time = None
                    continue

                log_sequence_index += 1
                previous_time = action_time
            
            #If line is found in the sequence but isn't the correct one reset index
            elif re.sub(LINE_TIME_PREFIX_RE, "", line) in LOG_REGEX_SEQUENCE:
                log_sequence_index = 0
                previous_time = None
                
    print(step_time_sum)

    labels = [
        "RefactoringMiner", 
        "Refactoring type sum and time average",
        "Commit diff calculation",
        "Dev effort collection",
        "Issue data collection"
    ]

    time_object = {
        labels[0]:  step_time_sum[0].total_seconds(),
        labels[1]:  step_time_sum[1].total_seconds(),
        labels[2]:  step_time_sum[2].total_seconds(),
        labels[3]:  step_time_sum[3].total_seconds(),
        labels[4]: step_time_sum[4].total_seconds(),
        "total_time": total_time.total_seconds()
    } 

    print(json.dumps(time_object))

    ax = plt.subplot()
    ax.pie([i.total_seconds() for i in step_time_sum], labels=labels)
    plt.show()



def draw_and_save_inter_commit_time_histogram():
    output_dirs = os.listdir(OUTPUT_ROOT_DIR)
    average_times = []
    for dir in output_dirs:
        try:
            with open(f"{OUTPUT_ROOT_DIR}/{dir}/{REFACTORING_FILE}", "r") as refactoring_file:
                json_obj = json.loads(refactoring_file.read())
                average_refactor_time = json_obj['average_time_between_refactors']
                match = re.search(
                    r"(?:(?P<days>\d+) day[s]?, )?(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)(?:.(?P<milliseconds>\d+))?",
                    average_refactor_time
                )
                days = int(match.group("days")) if match.group("days") else 0
                time = timedelta(
                    days=days,
                    hours=int(match.group("hours")),
                    minutes=int(match.group("minutes")),
                    seconds=int(match.group("minutes"))
                )

                average_times.append((time.total_seconds() / 60) / 60)
        except Exception as e:
            print(e)
    
    average_times = [i for i in average_times if i > 0]
    print(sorted(average_times))
    x_axis_ticks = [i for i in range(0, 336, 24)]
    ax = plt.subplot()
    ax.hist(average_times, bins=14, 
            range = (0,336), 
            color="pink", 
            edgecolor="black"
    )
    plt.xlabel("Average time between refactors in hours")
    plt.ylabel("Repositories")
    plt.xticks(x_axis_ticks)
    plt.show()



def main():
    draw_and_save_inter_commit_time_histogram()
    estimate_mining_time_division()


if __name__ == "__main__":
    main()

