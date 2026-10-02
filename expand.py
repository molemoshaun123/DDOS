import sys
with open('generate_submission.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_content = []
for line in lines:
    new_content.append(line)
    if 'add_para("\\nTable 5: Attribution comparison' in line:
        new_content.append('''add_para(
    "To fully understand the performance of COBT, it is instructive to examine the failure modes of the "
    "baseline methods in detail. The 'Fan-out' baseline and the 'Degree Centrality' baseline represent the "
    "most intuitive, naive approaches to attribution in a network context: simply finding the host that talks "
    "to the most other hosts. While this heuristic has some merit in highly restricted, isolated environments, "
    "it breaks down completely in realistic network topologies for several reasons."
)
add_para(
    "First, consider the role of legitimate infrastructure. In any enterprise or ISP network, certain hosts "
    "are designed to have massive fan-out and high degree centrality. DNS resolvers, active directory domain "
    "controllers, network time protocol (NTP) servers, load balancers, and centralized update servers routinely "
    "communicate with thousands of endpoints. When an attribution algorithm relies solely on aggregate contact "
    "volume or graph degree, these legitimate infrastructure nodes will consistently dominate the top ranks. "
    "This phenomenon is clearly visible in our limitation scenarios, particularly the decoy botmaster "
    "experiment, where benign high-fanout hosts completely eclipsed the true botmaster in the baseline rankings. "
    "The baselines suffer from a fundamental inability to distinguish between 'normal high fan-out' and "
    "'anomalous burst fan-out'. This is precisely the gap that COBT's baseline deviation signal addresses by "
    "comparing the observed fan-out burst against the candidate's historical norm, effectively filtering out "
    "the structural high-degree nodes."
)
add_para(
    "Second, the naive baselines completely ignore the arrow of time. Causality in network attacks is strictly "
    "temporal: the command must precede the attack. A host might communicate with all 50 suspected bots during "
    "the analysis window, but if those communications occur *after* the bots have already begun their attack, "
    "that host cannot be the controller. It might be a vulnerability scanner reacting to the attack, a monitoring "
    "system probing the bots, or an entirely unrelated automated process. By discarding the precise timing "
    "information and treating the pre-attack window as a flat, unordered set of edges, the graph centrality "
    "and aggregate fan-out baselines throw away the most discriminative evidence available. COBT's temporal "
    "precedence signal, which estimates the probability density of the lag between contact and attack onset, "
    "is the only mechanism capable of enforcing this strict causal requirement."
)
add_para(
    "Finally, the baseline methods are highly vulnerable to evasion by proxying and distributed C2. If a botmaster "
    "uses a hierarchical proxy structure (as tested in our deep proxy scenario), the botmaster's direct fan-out "
    "and degree centrality are artificially minimized. The botmaster only contacts a handful of first-tier "
    "proxies. The baselines will therefore completely overlook the true botmaster and instead flag the lowest-tier "
    "proxies that actually contacted the bots. While COBT also struggles with deep proxies without payload "
    "inspection, its multi-signal fusion approach—particularly the betweenness centrality computed in the "
    "interaction graph—provides a much more robust mathematical framework for potentially tracing back through "
    "intermediate nodes than simple aggregate degree counting."
)\n''')

with open('generate_submission.py', 'w', encoding='utf-8') as f:
    f.writelines(new_content)
