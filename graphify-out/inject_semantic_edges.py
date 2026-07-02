import json

GRAPH_PATH = '/Users/rishetmehra/Desktop/Findinternships/POLARIS-clone/graphify-out/graph.json'

with open(GRAPH_PATH, 'r') as f:
    data = json.load(f)

if 'links' not in data:
    data['links'] = []

# Find existing AST nodes based on their class names
def find_node(label_substring):
    for n in data['nodes']:
        if label_substring in n.get('label', '') and n.get('file_type') != 'document':
            return n['id']
    return None

master_agent_id = find_node("MasterAgent")
sales_agent_id = find_node("SalesAgent")
verification_agent_id = find_node("VerificationAgent")
underwriting_agent_id = find_node("UnderwritingAgent")
sanction_agent_id = find_node("SanctionAgent")
state_machine_id = find_node("ConversationState")

# Add the high-level semantic nodes that wouldn't be found in code
polaris_id = "concept_polaris"
rishet_id = "person_rishet"

new_nodes = [
    {"id": polaris_id, "label": "POLARIS", "file_type": "project", "degree": 0, "community_name": "Project Root"},
    {"id": rishet_id, "label": "Rishet Mehra", "file_type": "person", "degree": 0, "community_name": "Author"}
]

for n in new_nodes:
    if not any(node.get("id") == n["id"] for node in data["nodes"]):
        data["nodes"].append(n)

# Define the relationships linking the AST nodes together conceptually
edges_to_add = [
    (polaris_id, rishet_id, "BUILT_BY"),
]

if master_agent_id:
    edges_to_add.append((polaris_id, master_agent_id, "ORCHESTRATOR"))
    if state_machine_id:
        edges_to_add.append((master_agent_id, state_machine_id, "MANAGES_STATE"))
    if sales_agent_id:
        edges_to_add.append((master_agent_id, sales_agent_id, "INITIALIZES"))
    if verification_agent_id:
        edges_to_add.append((master_agent_id, verification_agent_id, "INITIALIZES"))
    if underwriting_agent_id:
        edges_to_add.append((master_agent_id, underwriting_agent_id, "INITIALIZES"))
    if sanction_agent_id:
        edges_to_add.append((master_agent_id, sanction_agent_id, "INITIALIZES"))

added_count = 0
for src, tgt, rel in edges_to_add:
    if not src or not tgt:
        continue
    # Check for exact edge match
    exists = any(e.get('source') == src and e.get('target') == tgt and e.get('relation') == rel for e in data['links'])
    if not exists:
        data['links'].append({
            "source": src,
            "target": tgt,
            "relation": rel,
            "weight": 1.0,
            "confidence": "EXTRACTED",
            "confidence_score": 1.0,
            "source_file": "manual_injection"
        })
        added_count += 1

# Recalculate node degrees based on new edges
for node in data["nodes"]:
    nid = node["id"]
    deg = sum(1 for e in data["links"] if e["source"] == nid or e["target"] == nid)
    node["degree"] = deg

with open(GRAPH_PATH, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Successfully injected {added_count} high-level semantic edges linking the POLARIS architecture.")
