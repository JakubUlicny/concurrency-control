import subprocess
from typing import Tuple, Optional

def run_cmd(cmd: str, realtime: bool = False, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    if realtime:
        # 实时输出模式
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout = []
        try:
            for line in process.stdout:
                print(line, end="")
                stdout.append(line)
            
            returncode = process.wait(timeout=timeout)
            stderr = process.stderr.read()
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", "Command timed out"

        return returncode, "".join(stdout), stderr

    else:
        # 一次性捕获模式
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
