# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 10:53:36 2026

@author: A.Harshitha
"""

import requests

def Flag_Check(vin_number):
    BASE_URL = "http://10.121.2.107:3000/vehicles/flashFile"

    # URLs for both checks
    url_Flashing = f"{BASE_URL}/{vin_number}/0010/CZ14001"
    url_Static = f"{BASE_URL}/{vin_number}/0020/CZ14002"
    url_DAQ = f"{BASE_URL}/{vin_number}/0030/CZ14003"

    def get_result(url):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return None
            data = response.json().get("data", {})
            return data.get("result")   # result can be "OK", "NOK" or None
        except:
            return None

    Flashing_Result = get_result(url_Flashing)
    Static_Result = get_result(url_Static)
    DAQ_Result = get_result(url_DAQ)

    # ✅ Null case check first
    if Flashing_Result == "Null":
        print("NOK - Null")
        return False, "Null"

    if Static_Result == "Null":
        print("NOK - Null")
        return False, "Null"

    if DAQ_Result == "Null":
        print("NOK - Null")
        return False, "Null"

    # ✅ Evaluate status logic
    if Flashing_Result == "OK":
        print("OK")
        return True, "OK"

    if Static_Result == "OK":
        print("OK")
        return True, "OK"

    if DAQ_Result == "OK":
        print("OK")
        return True, "OK"

    # Fallback for unexpected content
    return False, "Flag Check Error"


if __name__ == "__main__":
    Flag_Check(vin_number="MD626AM47S1C00070")
