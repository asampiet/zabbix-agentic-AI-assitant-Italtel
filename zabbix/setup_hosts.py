#!/usr/bin/env python3
import requests
import json

ZABBIX_URL = "http://localhost:13080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASS = "zabbix"

# Network nodes to monitor
HOSTS = {
    "Core Routers": [
        {"name": "core-1", "ip": "172.30.0.11"},
        {"name": "core-2", "ip": "172.30.0.12"},
        {"name": "core-3", "ip": "172.30.0.13"},
    ],
    "Transport Routers": [
        {"name": "transport-1", "ip": "172.30.0.21"},
        {"name": "transport-2", "ip": "172.30.0.22"},
        {"name": "transport-3", "ip": "172.30.0.23"},
        {"name": "transport-4", "ip": "172.30.0.24"},
        {"name": "transport-5", "ip": "172.30.0.25"},
    ],
    "Access Routers": [
        {"name": "access-1", "ip": "172.30.0.31"},
        {"name": "access-2", "ip": "172.30.0.32"},
        {"name": "access-3", "ip": "172.30.0.33"},
        {"name": "access-4", "ip": "172.30.0.34"},
    ],
}

def zabbix_request(method, params, auth=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    if auth:
        payload["auth"] = auth
    resp = requests.post(ZABBIX_URL, json=payload)
    return resp.json()

# Login
print("Logging in to Zabbix...")
result = zabbix_request("user.login", {"username": ZABBIX_USER, "password": ZABBIX_PASS})
auth_token = result.get("result")
if not auth_token:
    print(f"Login failed: {result}")
    exit(1)
print(f"Logged in successfully")

# Get template ID for ICMP Ping
print("Getting ICMP Ping template...")
result = zabbix_request("template.get", {"filter": {"host": "ICMP Ping"}}, auth_token)
if not result.get("result"):
    # Try alternative template name
    result = zabbix_request("template.get", {"search": {"name": "ICMP"}}, auth_token)
templates = result.get("result", [])
template_id = templates[0]["templateid"] if templates else None
print(f"Template ID: {template_id}")

# Create host groups
group_ids = {}
for group_name in HOSTS.keys():
    print(f"Creating host group: {group_name}")
    result = zabbix_request("hostgroup.get", {"filter": {"name": group_name}}, auth_token)
    if result.get("result"):
        group_ids[group_name] = result["result"][0]["groupid"]
        print(f"  Group exists: {group_ids[group_name]}")
    else:
        result = zabbix_request("hostgroup.create", {"name": group_name}, auth_token)
        if result.get("result"):
            group_ids[group_name] = result["result"]["groupids"][0]
            print(f"  Created: {group_ids[group_name]}")
        else:
            print(f"  Error: {result}")

# Create hosts
for group_name, hosts in HOSTS.items():
    group_id = group_ids.get(group_name)
    if not group_id:
        continue
    
    for host in hosts:
        print(f"Creating host: {host['name']}")
        
        # Check if host exists
        result = zabbix_request("host.get", {"filter": {"host": host["name"]}}, auth_token)
        if result.get("result"):
            print(f"  Host exists, skipping")
            continue
        
        host_params = {
            "host": host["name"],
            "name": host["name"].replace("-", " ").title(),
            "groups": [{"groupid": group_id}],
            "interfaces": [{
                "type": 1,  # Agent
                "main": 1,
                "useip": 1,
                "ip": host["ip"],
                "dns": "",
                "port": "10050"
            }],
            "tags": [
                {"tag": "network_type", "value": group_name.split()[0].lower()},
                {"tag": "environment", "value": "lab"}
            ]
        }
        
        if template_id:
            host_params["templates"] = [{"templateid": template_id}]
        
        result = zabbix_request("host.create", host_params, auth_token)
        if result.get("result"):
            print(f"  Created: {result['result']['hostids'][0]}")
        else:
            print(f"  Error: {result.get('error', result)}")

print("\nDone! Hosts configured in Zabbix.")
print("Access Zabbix at: http://localhost:13080")
