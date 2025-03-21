from src.submit import Problem
from src.crud import get_problem
from src.database import SessionLocal

def get_specific_problem(difficulty: list[bool], problem_id: int) -> dict:
    db = SessionLocal()

    try:
        problem = get_problem(db, difficulty, problem_id)
        return {"name": problem.problem_name, "description": problem.problem_description, "difficulty": problem.problem_difficulty, "test_cases": problem.test_cases, "function_signature": problem.function_signature, "any_order": problem.any_order}
    
    finally:
        db.close()


def test_any_order():
    p = get_specific_problem([True, True, True], 1)
    problem = Problem(100, p)

    code = """
def twoSum(nums: list[int], target: int) -> list[int]:
    hashmap = {}
    for i in range(len(nums)):
        complement = target - nums[i]
        if complement in hashmap:
            return [i, hashmap[complement]]
        hashmap[nums[i]] = i
    # Return an empty list if no solution is found
    return []
"""

    r = problem.submit_code(code)

    print(r)
    assert "status" in r
    assert r["status"] == "Accepted"