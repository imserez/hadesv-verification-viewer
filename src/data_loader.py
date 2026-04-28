import json, re

def load_raw_trace(path: str) -> str:
    with open(path, "r") as file:
        return file.read().strip()

def fix_json_string(raw_data: str) ->str:
    if (raw_data.endswith(",")):
        raw_data = raw_data[:-1]

    if not raw_data.endswith("]"):
        last_brace = raw_data.rfind("}")
        if (last_brace != -1):
            raw_data = raw_data[:last_brace+1] +"\n]"
        else:
            raw_data = raw_data + "\n]"

    raw_data = re.sub(r"}\s*{", "},\n{", raw_data)
    return raw_data

def parse_pipeline_trace(raw_data: str) ->str:
    return json.loads(raw_data)

def find_mismatch_cycles(data: list) -> list[int]:
    mismatch_indexs = []

    for i, status in enumerate(data):
        if not status:
            continue

        d_vals = status.get("dut_values", {})
        r_vals = status.get("ref_values", {})

        for key in d_vals:
            if str(d_vals.get(key)) != str(r_vals.get(key)):
                mismatch_indexs.append(i)
                break

    return mismatch_indexs

def find_error_cycles(data:list) -> list[int]:
    error_indexs = []

    for i, status in enumerate(data):
        if not status:
            continue

        error = status.get("error", {})

        if (error == 1):
            error_indexs.append(i)
    return error_indexs