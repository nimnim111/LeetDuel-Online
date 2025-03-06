import json
import subprocess


with open("problems.json", "r") as f:
    problems = json.load(f)
    

class Problem:
    def __init__(self, language_id, problem):
        self.language_id = language_id
        self.problem = problem
        self.stdinput = json.dumps([json.loads(test_case["input"]) for test_case in problem["test_cases"]])


    def submit_code(self, code: str, timeout: int = 10) -> str:
        """Executes code with a timeout to prevent infinite loops."""
        code = "import sys\nimport json\n" + code + """
input_data = sys.stdin.read().strip()
test_cases = json.loads(input_data)
results = [run(*args) for args in test_cases]
for result in results:
    print(result)
        """
        print(self.stdinput)
        try:
            result = subprocess.run(
                ["docker", "run", "-i", "--rm", "--memory=100m", "--cpu-shares=50", "code-runner", "python3", "-c", code],
                input=self.stdinput,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode != 0:
                return {"message": result.stderr, "status": "Failed"}
            
            print(result.stdout)
            return self.check_test_cases(result.stdout, "N/A")

        except subprocess.TimeoutExpired:
            return {"message": "Time limit exceeded", "status": "Failed"}
        except Exception as e:
            return {"message": str(e), "status": "Failed"}
        

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