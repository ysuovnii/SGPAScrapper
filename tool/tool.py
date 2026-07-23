import requests
from bs4 import BeautifulSoup
import csv
import time 

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RESET = "\033[0m"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/143.0.0.0 Safari/537.36"
})

student_pass = []
student_fail = []

# 24 i 3 0 81  
# {batch} {branch} {sem} {section} {roll}

batch = input("Enter batch (e.g., 24): ")
batch_LE = int(batch) + 1
sem = int(input("Enter semester (e.g., 3): "))

roll_range = [(sem*1000+1, sem*1000+90), (sem*1000+101, sem*1000+190)]
roll_range_LE = [(sem*1000+90, sem*1000+99), (sem*1000+190, sem*1000+199)]

branch_list = ['c', 'i', 'b', 't', 'e', 'm', 'v'] 
branch_map = {
    'c': 'Computer Science',
    'i': 'Information Technology',
    'b': 'Computer Science Business Studies',
    't': 'Electronics and Telecommunication',
    'e': 'Electronics and Instrumentation',
    'm': 'Mechanical',
    'v': 'Civil',
}

def fetch(URL, branch, retries):
    for attempt in range(1, retries+1):
        try:
            res = session.get(URL, timeout=5, verify=False) # verify = True
            soup = BeautifulSoup(res.text, 'html.parser')

            nameTag = soup.find(string="Student Name")
            rollTag = soup.find(string="Roll Number")
            verdictTag = soup.find(string="Result")
            cgTag = soup.find(string="SGPA")

            if nameTag and rollTag and verdictTag and cgTag:
                name = nameTag.find_next('td').text.strip()
                roll = rollTag.find_next('td').text.strip()
                verdict = verdictTag.find_next('td').text.strip()
                cg = float(cgTag.find_next('td').text.strip())

                record = {
                    "branch" : branch, 
                    "name": name,
                    "roll": roll,
                    "verdict": verdict,
                    "cg": cg
                }

                print(f"{GREEN}{roll} {name} : {cg} {verdict}{RESET}")

                if verdict == "Fail":
                    student_fail.append(record)
                else :
                    student_pass.append(record)

                return  

        except requests.exceptions.Timeout:
            print(f"{YELLOW}Timeout attempt {attempt}: {URL}{RESET}")
            time.sleep(1)

        except Exception as e:
            print(f"{RED}Error: {e} | URL: {URL}{RESET}")
            break  

    print(f"{RED}Failed to fetch after {retries} attempts: {URL}{RESET}")
   
def generateURL():
    total = len(branch_list) * sum(end - start for start, end in roll_range)
    done = 0
    for branch in branch_list:
        branchName = branch_map.get(branch, 'Unknown Branch')
        if branch in ['e', 'm', 'v']: 
            for roll in range(sem*1000+1, sem*1000+90):
                url = f"https://results.ietdavv.edu.in/DisplayStudentResult?rollno={batch}{branch}{roll}&typeOfStudent=Regular"

                fetch(url, branchName, 3)
                done += 1
                print(f"[{done}/{total}] fetched", end="\r")
                time.sleep(0.3)
        else : 
            for start, end in roll_range:
                for roll in range(start, end):
                    url = f"https://results.ietdavv.edu.in/DisplayStudentResult?rollno={batch}{branch}{roll}&typeOfStudent=Regular"

                    fetch(url, branchName, 3)
                    done += 1
                    print(f"[{done}/{total}] fetched", end="\r")
                    time.sleep(0.3)

def generateURL_LE():
    total = len(branch_list) * sum(end - start for start, end in roll_range_LE)
    done = 0
    for branch in branch_list:
        branchName = branch_map.get(branch, 'Unknown Branch')
        if branch in ['e', 'm', 'v']: 
            for roll in range(sem*1000+90, sem*1000+99):
                url = f"https://results.ietdavv.edu.in/DisplayStudentResult?rollno={batch_LE}{branch}{roll}&typeOfStudent=Regular"

                fetch(url, branchName, 3)
                done += 1
                print(f"[{done}/{total}] fetched", end="\r")
                time.sleep(0.3)
        else : 
            for start, end in roll_range_LE:
                for roll in range(start, end):
                    url = f"https://results.ietdavv.edu.in/DisplayStudentResult?rollno={batch_LE}{branch}{roll}&typeOfStudent=Regular"

                    fetch(url, branchName, 3)
                    done += 1
                    print(f"[{done}/{total}] fetched", end="\r")
                    time.sleep(0.3)    

def rank_students():
    all_students = student_pass + student_fail

    all_students.sort(
        key=lambda x: (x["verdict"] == "Fail", -x["cg"])
    )

    rank = 1
    prev_key = None  

    for idx, student in enumerate(all_students):
        current_key = (student["verdict"], student["cg"])

        if current_key != prev_key:
            rank = idx + 1

        student["rank"] = rank
        prev_key = current_key

    return all_students

def write_csv(all_students):
    with open(f"New_Ver_{batch}_Sem_{sem}_Result.csv", "w", newline="") as f:
        fieldnames = ["rank", "branch", "name", "roll", "cg", "verdict"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for s in all_students:
            writer.writerow(s)

if __name__ == "__main__":
    start_time = time.time()
    generateURL()
    generateURL_LE()
    print()

    all_students = rank_students()

    print(f"\nTotal students: {len(all_students)}")
    print(f"Pass: {len(student_pass)}")
    print(f"Fail: {len(student_fail)}")

    write_csv(all_students)

    print(f"\nExecution Time: {time.time() - start_time:.2f} seconds")
