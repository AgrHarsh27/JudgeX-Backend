import tempfile
import subprocess
import os
import time
def execute_code(source_code,input_data, language):
    language = language.lower()
    if language == 'python':
        temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False
        )
        temp_file.write(source_code)
        temp_file.close()
        file_path = temp_file.name
        try:
            start_time = time.time()
            result = subprocess.run(
            ['python',file_path],
            capture_output=True,
            text=True,
            input =  input_data,
            timeout=2
            )
            execution_time = time.time()-start_time
            if result.returncode != 0: 
                return "RUNTIME_ERROR" , result.stderr.strip(), execution_time
            return "OK" , result.stdout.strip(),execution_time
        except subprocess.TimeoutExpired:
            execution_time = time.time()-start_time
            return "TIME_LIMIT_EXCEEDED", "", execution_time
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    else: 
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.cpp',
            delete= False
        )
        temp_file.write(source_code)
        temp_file.close()
        file_path = temp_file.name
        binary_path = file_path.replace(".cpp", "")
        try:
            compile_result = subprocess.run(
                ['g++',file_path,'-o',binary_path],
                capture_output=True,
                text=True,
            )
            if compile_result.returncode != 0: 
                return "COMPILATION_ERROR" , compile_result.stderr.strip(), 0
            start_time = time.time()
            if os.name=="nt": 
                run_result = subprocess.run(
                    [binary_path  + ".exe"],
                    capture_output=True,
                    text=True,
                    input=input_data,
                    timeout=2
                )
            else:
                run_result = subprocess.run(
                    ["./"+binary_path],
                    capture_output=True,
                    text=True,
                    input=input_data,
                    timeout=2
                )
            execution_time = time.time()-start_time
            if run_result.returncode!=0: 
                return "RUNTIME_ERROR",run_result.stderr.strip(),execution_time
            return "OK",run_result.stdout.strip(),execution_time
        except subprocess.TimeoutExpired:
            execution_time = time.time()-start_time
            return "TIME_LIMIT_EXCEEDED", "", execution_time
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.name == "nt":
                if os.path.exists(binary_path + ".exe"):
                    os.remove(binary_path + ".exe")
            else :
                if os.path.exists(binary_path):
                    os.remove(binary_path)