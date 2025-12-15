#!/usr/bin/env python3
import requests

ZABBIX_URL = "http://localhost:13080/api_jsonrpc.php"

def zabbix_request(method, params, auth=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    if auth:
        payload["auth"] = auth
    return requests.post(ZABBIX_URL, json=payload).json()

# Login
result = zabbix_request("user.login", {"username": "Admin", "password": "zabbix"})
auth = result["result"]

# Get all network hosts
result = zabbix_request("host.get", {
    "filter": {"name": ["core-1", "core-2", "core-3", 
                        "transport-1", "transport-2", "transport-3", "transport-4", "transport-5",
                        "access-1", "access-2", "access-3", "access-4"]},
    "selectInterfaces": "extend"
}, auth)

for host in result.get("result", []):
    host_id = host["hostid"]
    host_name = host["host"]
    
    # Get current interface
    interfaces = host.get("interfaces", [])
    if interfaces:
        interface_id = interfaces[0]["interfaceid"]
        ip = interfaces[0]["ip"]
        
        # Delete agent interface
        zabbix_request("hostinterface.delete", [interface_id], auth)
        
        # Create SNMP interface (type 2) - works for ICMP template without agent
        result = zabbix_request("hostinterface.create", {
            "hostid": host_id,
            "type": 2,  # SNMP
            "main": 1,
            "useip": 1,
            "ip": ip,
            "dns": "",
            "port": "161",
            "details": {
                "version": 2,
                "community": "public"
            }
        }, auth)
        print(f"Updated {host_name}: {ip}")

print("\nDone! Hosts now use SNMP interface for ICMP monitoring.")
