import sys

with open('generate_submission.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_chunk = """)
    "probabilistically stamp packets with path information, allowing the victim to reconstruct the attack path. "
    "However, PPM requires router cooperation across administrative domains and is ineffective against attacks "
    "using botnets with real (non-spoofed) source IPs."
)
add_para(
    "Stepping-stone detection research (Zhang and Paxson, 2000) addressed the problem of tracing interactive "
    "sessions through chains of compromised hosts. While conceptually related to our proxy-chain attribution, "
    "stepping-stone detection assumes interactive SSH-like sessions with detectable timing correlations, which "
    "differ fundamentally from the short, bursty C2 commands in botnet scenarios."
)"""

good_chunk = """)"""

if bad_chunk in content:
    content = content.replace(bad_chunk, good_chunk)
    with open('generate_submission.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed successfully")
else:
    print("Bad chunk not found")
