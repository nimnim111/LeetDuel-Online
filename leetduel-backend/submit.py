from dotenv import load_dotenv
import os
import requests
import json
import sys

load_dotenv(dotenv_path="../.env.local")
judge0_api_key = os.getenv("JUDGE0_API_KEY")
language_id = 100

with open("problems.json", "r") as f:
    problems = json.load(f)

class Problem:
    def __init__(self, code, language_id, problem_id):
        self.code = code
        self.language_id = language_id
        self.problem = problems[problem_id]
        self.stdinput = ""


    def add_test_cases(self, input_code):
        test_cases = self.problem["test_cases"]
        for test_case in test_cases:
            self.stdinput += f"print({test_case['input']})\n"


    def submit_code(self, code, language_id):
        code = "import sys\n" + code + "\n" + "for line in sys.stdin:\nprint(run(line.strip()))"

        url = "https://judge0-ce.p.rapidapi.com/submissions/?base64_encoded=false&wait=false"
        headers = {
            "content-type": "application/json",
            "x-rapidapi-key": judge0_api_key,
            "x-rapidapi-host": "judge0-ce.p.rapidapi.com",
        }
        data = {
            "source_code": code,
            "language_id": language_id,
            "stdin": self.stdinput,
            "cpu_time_limit": 5,
            "wall_time_limit": 10,
        }
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 201:
            return response

        response_data = response.json()
        
        if response_data["status"]["description"] != "Accepted":
            return response_data
        
        token = response_data["token"]

        url = f"https://judge0-ce.p.rapidapi.com/submissions/{token}?base64_encoded=false"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return response
        
        response_data = response.json()
        return self.check_test_cases(response_data["stdout"])
        

    def check_test_cases(self, data):
        test_cases = self.problem["test_cases"]
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