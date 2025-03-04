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
    def __init__(self, language_id, problem, api_key):
        self.language_id = language_id
        self.problem = problem
        self.stdinput = ""
        self.api_key = api_key


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
            "x-rapidapi-key": self.api_key,
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

        print(response_data)

        if "stderr" in response_data and response_data["stderr"]:
            return response_data["stderr"]
        
        return self.check_test_cases(response_data["stdout"])
        

    def check_test_cases(self, data):
        test_cases = self.problem["tests"]
        if not data:
            return "No output"
        data = data.split("\n")[:-1]
        print(test_cases, data)
        count = 0
        r = {"status": "Accepted", "total test cases": len(test_cases)}

        for i in range(len(data)):
            if data[i] != test_cases[i]["output"]:
                r["status"] = "Failed"

                if "test_case" not in r:
                    r["test_case"] = i
                continue

            count += 1
        
        r["passed test cases"] = count
        print(r["status"])
        return r
    
    
    def get_problem_title(self):
        return self.problem["title"]
    

    def get_problem_description(self):
        return self.problem["description"]