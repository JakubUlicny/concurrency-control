import os
import runcmd
import ast 
from log import logger

PIPELINE_CM = os.environ.get("PIPELINE_CM")
FINISH_RUN_KEY = "wait_finish_runs"
FINISH_TASK_KEY = "wait_finish_task"

def get_wait_finish_runs():
    cmd = "oc get cm {} -o json | jq -r '.data[\"{}\"]'".format(PIPELINE_CM, FINISH_RUN_KEY)
    code, out, _ = runcmd.run_cmd(cmd)
    if code==0 and out.strip() != "null" :
        lst = ast.literal_eval(out.strip())
        return lst
    else:
        print(f"failed to find in configmap {PIPELINE_CM}")
        return None

def get_wait_finish_task():
    cmd = "oc get cm {} -o json | jq -r '.data[\"{}\"]'".format(PIPELINE_CM, FINISH_TASK_KEY)
    code, out, _ = runcmd.run_cmd(cmd)
    if code==0 and out.strip() != "null" :
        lst = ast.literal_eval(out.strip())
        return lst
    else:
        print(f"failed to find in configmap {PIPELINE_CM}")
        return None

def write_cm(cm_name, key, value):
    cmd = f"oc set data configmap {cm_name} {key}=\"{value}\""
    code, out, _ = runcmd.run_cmd(cmd)
    if code == 0:
        return True
    else:
        logger.error(f"failed to change {key} status to {value}")
        logger.error(out)
        return False

def append_wait_finish_run(new_elelment):
    origi_list = get_wait_finish_runs()
    origi_list.append(new_elelment)
    update_wait_finish_run(origi_list)

def update_wait_finish_run(wait_finish_list):
    if not write_cm(PIPELINE_CM, FINISH_RUN_KEY, wait_finish_list):
        logger.error(f"failed to update config map {PIPELINE_CM} {FINISH_RUN_KEY}")

def append_wait_task(new_elelment):
    origi_list = get_wait_finish_task()
    origi_list.append(new_elelment)
    update_wait_finish_task(origi_list)

def update_wait_finish_task(wait_finish_list):
    if not write_cm(PIPELINE_CM, FINISH_TASK_KEY, wait_finish_list):
        logger.error(f"failed to update config map {PIPELINE_CM} {FINISH_TASK_KEY}")
