import json
import subprocess
import time
from ratelimit import limits, RateLimitException

from src.classes.ListNode import ListNode, linkedList



class Problem:


    def __init__(self, language_id: int, problem: dict):
        self.language_id = language_id
        self.problem = problem
        self.stdinput = json.dumps([test_case["input"] for test_case in problem["test_cases"]])


    def submit_code(self, code: str, timeout: int = 2) -> dict:
        function_name = self.problem["function_signature"].split("(")[0][4:]
        code = """
import sys
import json
import time

class ListNode(object):
    def __init__(self, x=0, next=None):
        self.val = x
        self.next = next

    def __repr__(self):
        r = []
        copy = self
        while copy:
            r.append(copy.val)
            copy = copy.next

        return str(r)


def linkedList(a):
    if not a:
        return None
    
    head = curr = ListNode(a[0])
    for i in a[1:]:
        curr.next = ListNode(i)
        curr = curr.next

    return head
""" + f"""
{code}
input_data = sys.stdin.read().strip()
test_cases = json.loads(input_data)
start_time = time.time_ns()
results = []
for args in test_cases:
    print("|")
    results.append({function_name}(*eval(args)))

for result in results:
    print(result)
print(int((time.time_ns() - start_time) / 1e6))
        """

        try:
            result = self.run_subprocess(code, timeout)

            if result.returncode != 0:
                return {"message": result.stderr, "status": "Failed"}
            
            return self.check_test_cases(result.stdout)

        except subprocess.TimeoutExpired:
            return {"message": "Time limit exceeded", "status": "Failed"}
        
        except RateLimitException:
            return {"message": "Rate limited! Please wait 5 seconds and try again.", "status": "Failed"}
        
        except Exception as e:
            return {"message": str(e), "status": "Failed"}
        

    def check_test_cases(self, data: str) -> dict:
        test_cases = self.problem["test_cases"]
        any_order = self.problem["any_order"]

        if not data:
            return {"message": "No output", "status": "Failed"}

        data = data.split("\n")[:-1]
        time = data.pop()

        count = 0
        failed_index = -1

        r = {"status": "Accepted", "total test cases": len(test_cases), "time": time}

        n = len(test_cases)
        output = "\n".join(data[:-n])
        output_list = output.split("|\n")[1:]
        data = data[-n:]

        for i in range(len(data)):
            
            
            user_output = data[i]
            test_output = test_cases[i]["output"]

            try:
                if any_order and isinstance(eval(user_output), list) and isinstance(eval(test_output), list):
                    user_output = eval(user_output)
                    test_output = eval(test_output)

                    user_output.sort()
                    test_output.sort()

            except Exception as e:
                print(e)

            if user_output != test_output:
                r["status"] = "Failed"
                if failed_index == -1:
                    failed_index = i
                    r["stdout"] = output_list[i]

                continue

            count += 1
        
        r["passed test cases"] = count
        
        if failed_index != -1:
            r["failed_test"] = f"Input: {str(eval(test_cases[failed_index]['input']))}\nExpected {test_cases[failed_index]['output']}, got {data[failed_index]}"

        return r
    

    @limits(calls=5, period=10)
    def run_subprocess(self, code, timeout):
        return subprocess.run(
            ["python3", "-c", code],
            input=self.stdinput,
            capture_output=True,
            text=True,
            timeout=timeout
        )