import requests
import json
import sys
import time


with open("problems.json", "r") as f:
    problems = json.load(f)
    

class Problem:
    def __init__(self, language_id, problem, api_key):
        self.language_id = language_id
        self.problem = problem
        self.stdinput = ""
        self.api_key = api_key


    def add_test_cases(self):
        test_cases = self.problem["test_cases"]
        self.stdinput = json.dumps([json.loads(test_case["input"]) for test_case in test_cases])
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
        description = "Processing"

        while description == "Processing":

            time.sleep(2)

            url = f"https://judge0-ce.p.rapidapi.com/submissions/{token}?base64_encoded=false"
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return {"message": "Internal error occurred", "status": "Failed"}
            
            response_data = response.json()
            description = response_data["status"]["description"]

        print(response_data)

        if "stderr" in response_data and response_data["stderr"]:
            return {"message": response_data["stderr"], "status": "Failed"}
        
        if "message" in response_data and response_data["message"] == "Time limit exceeded":
            return {"message": response_data["message"] + " (" + response_data["time"] + "s).", "status": "Failed"}
        
        return self.check_test_cases(response_data["stdout"], response_data["time"])
        

    def check_test_cases(self, data, time):
        test_cases = self.problem["test_cases"]
        if not data:
            return "No output"
        data = data.split("\n")[:-1]
        print(test_cases, data)
        count = 0
        r = {"status": "Accepted", "total test cases": len(test_cases), "time": time}

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