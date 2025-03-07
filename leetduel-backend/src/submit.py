import json
import subprocess
import time



class Problem:


    def __init__(self, language_id: int, problem: dict):
        self.language_id = language_id
        self.problem = problem
        self.stdinput = json.dumps([json.loads(test_case["input"]) for test_case in problem["test_cases"]])


    def submit_code(self, code: str, timeout: int = 5) -> str:
        code = "import sys\nimport json\n" + code + """
input_data = sys.stdin.read().strip()
test_cases = json.loads(input_data)
results = [run(*args) for args in test_cases]
for result in results:
    print(result)
        """
        
        start_time = time.time_ns()

        try:
            result = subprocess.run(
                ["docker", "run", "-i", "--rm", "--memory=100m", "--cpu-shares=50", "code-runner", "python3", "-c", code],
                input=self.stdinput,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            interval = int((time.time_ns() - start_time) / 1e6)
            if result.returncode != 0:
                return {"message": result.stderr, "status": "Failed"}
            
            return self.check_test_cases(result.stdout, str(interval))

        except subprocess.TimeoutExpired:
            return {"message": "Time limit exceeded", "status": "Failed"}
        
        except Exception as e:
            return {"message": str(e), "status": "Failed"}
        

    def check_test_cases(self, data: dict, time: int) -> dict:
        test_cases = self.problem["test_cases"]
        if not data:
            return {"message": "No output", "status": "Failed"}
        
        data = data.split("\n")[:-1]
        count = 0
        failed_index = -1

        r = {"status": "Accepted", "total test cases": len(test_cases), "time": time}

        for i in range(len(data)):
            if data[i] != test_cases[i]["output"]:
                r["status"] = "Failed"
                if failed_index == -1:
                    failed_index = i

                continue

            count += 1
        
        r["passed test cases"] = count
        
        if failed_index != -1:
            r["failed_test"] = "Input: " + test_cases[failed_index]["input"] + "\nExpected " + test_cases[failed_index]["output"] + ", got " + data[failed_index]

        return r