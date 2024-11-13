import scapy.all as scapy
import requests
import subprocess

def port_scan(target_ip, ports):
    packet = scapy.IP(dst=target_ip)/scapy.TCP(dport=ports)
    responses = scapy.sr(packet, timeout=1, verbose=0)
    open_ports = []
    for response in responses:
        if response.haslayer(scapy.TCP):
            if response.getlayer(scapy.TCP).flags == 0x12:
                open_ports.append(response.getlayer(scapy.TCP).dport)
    return open_ports

def xss_detect(target_url):
    payload = "<script>alert('XSS')</script>"
    response = requests.get(target_url, params={"input": payload})
    if payload in response.text:
        return True
    else:
        return False

def sql_injection_detect(target_url):
    process = subprocess.Popen(["sqlmap", "-u", target_url], stdout=subprocess.PIPE)
    output = process.communicate()[0].decode("utf-8")
    if "vulnerable" in output:
        return True
    else:
        return False

def generate_report(target_ip, open_ports, xss_vulnerable, sql_vulnerable):
    report = """
*Vulnerability Report*

*Target System:* {}

*Open Ports:*

{}
""".format(target_ip, "\n* ".join(map(str, open_ports)))

    if xss_vulnerable:
        report += """
*XSS Vulnerabilities:*

* {}
""".format(target_url)

    if sql_vulnerable:
        report += """
*SQL Injection Vulnerabilities:*

* {}
""".format(target_url)

    report += """
*Recommendations:*

* Close open ports to prevent unauthorized access.
* Fix XSS vulnerabilities by properly sanitizing user input.
* Fix SQL Injection vulnerabilities by using prepared statements and input validation.
"""

    return report

target_ip = "192.168.1.100"
ports = [21, 22, 80, 443]
target_url = "http://example.com/vulnerable_page"

open_ports = port_scan(target_ip, ports)
xss_vulnerable = xss_detect(target_url)
sql_vulnerable = sql_injection_detect(target_url)

report = generate_report(target_ip, open_ports, xss_vulnerable, sql_vulnerable)
print(report)