from dotenv import load_dotenv
import os
import requests
import json
import sys
import time

load_dotenv(dotenv_path="../.env.local")
judge0_api_key = os.getenv("JUDGE0_API_KEY")
language_id = 100

with open("problems.json", "r") as f:
    problems = json.load(f)

class Problem:
    def __init__(self, language_id, problem_id):
        self.language_id = language_id
        self.problem = problems[problem_id]
        self.stdinput = ""


    def add_test_cases(self):
        test_cases = self.problem["tests"]
        self.stdinput = json.dumps([test_case["input"] for test_case in test_cases])
        return self.stdinput


    def submit_code(self, code):
        self.add_test_cases()

        code = "import sys\nimport json\n" + code + """
input_data = sys.stdin.read().strip()
test_cases = json.loads(input_data)
results = [run(*args) for args in test_cases]
for result in results:
    print(result)
        """

        url = "https://judge0-ce.p.rapidapi.com/submissions/?base64_encoded=false&wait=false"
        headers = {
            "content-type": "application/json",
            "x-rapidapi-key": judge0_api_key,
            "x-rapidapi-host": "judge0-ce.p.rapidapi.com",
        }
        data = {
            "source_code": code,
            "language_id": self.language_id,
            "stdin": self.stdinput,
            "cpu_time_limit": 5,
            "wall_time_limit": 10,
        }
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 201:
            return response

        response_data = response.json()
        print(response_data)
        token = response_data["token"]

        time.sleep(3)

        url = f"https://judge0-ce.p.rapidapi.com/submissions/{token}?base64_encoded=false"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return response
        
        response_data = response.json()

        if "error" in response_data:
            return response_data["error"]
        
        print(response_data)
        
        return self.check_test_cases(response_data["stdout"])
        

    def check_test_cases(self, data):
        test_cases = self.problem["tests"]
        if not data:
            return {"status": "Failed", "test_case": 0}
        data = data.split("\n")[:-1]
        count = 0
        r = {"status": "Accepted", "Total test cases": len(test_cases)}

        for i in range(len(data)):
            if data[i] != test_cases[i]["output"]:
                r["status"] = "Failed"

                if "test_case" not in r:
                    r["test_case"] = i
                continue

            count += 1
        
        r["Passed test cases"] = count
        return r
    
    
    def get_problem_title(self):
        return self.problem["title"]
    

    def get_problem_description(self):
        return self.problem["description"]
    


code = """
def run(nums, target):
    d = {}
    for i, num in enumerate(nums):
        if target - num in d:
            return [d[target - num], i]
        d[num] = i
    return []
"""

problem = Problem(language_id, "Two Sum")
print(problem.submit_code(code))