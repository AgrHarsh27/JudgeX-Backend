from execute_code import execute_code
def judge(problem, source_code, language):
    maxTime = 0
    for test_case in problem.test_cases:
        status,output, time = execute_code(source_code, test_case.input_data, language)
        maxTime = max(maxTime,time)
        if status == "TIME_LIMIT_EXCEEDED":
            return "Time Limit Exceeded",maxTime
        if status == "RUNTIME_ERROR":
            return "RunTime Error",maxTime
        if status == "COMPILATION_ERROR":
            return "Compilation ERROR",0
        if output.strip() != test_case.expected_output.strip():
            return "Wrong Answer",maxTime
    return "Accepted",maxTime