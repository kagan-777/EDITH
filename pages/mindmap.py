import json

import graphviz
import streamlit as st

from backend.mindmap import generate_mindmap
from backend.session import require_login, run_ai

st.set_page_config(page_title="AI Mind Map", page_icon="🧠", layout="wide")
user = require_login()

st.title("🧠 AI Mind Map Generator")
st.write("Generate a visual mind map from your uploaded study material.")


def create_graph(data):
    """Nodes use unique IDs, so repeated labels no longer merge into one node."""
    graph = graphviz.Digraph("MindMap")
    graph.attr(rankdir="TB")
    graph.node("root", data["root"], shape="box", style="filled", fillcolor="lightblue")
    for b, branch in enumerate(data["branches"]):
        bid = f"b{b}"
        graph.node(bid, branch["title"], shape="ellipse", style="filled", fillcolor="lightgreen")
        graph.edge("root", bid)
        for i, item in enumerate(branch["items"]):
            iid = f"{bid}_{i}"
            graph.node(iid, item, shape="note", style="filled", fillcolor="lightyellow")
            graph.edge(bid, iid)
    return graph


if st.button("🧠 Generate Mind Map"):
    mindmap = run_ai("Generating mind map...", generate_mindmap, user)
    if mindmap:
        st.session_state["mindmap_result"] = mindmap

mindmap = st.session_state.get("mindmap_result")
if mindmap:
    st.success("✅ Mind map ready")
    st.graphviz_chart(create_graph(mindmap))
    with st.expander("📄 JSON"):
        st.json(mindmap)
    st.download_button("📥 Download Mind Map (JSON)", json.dumps(mindmap, indent=2),
                       "EcoEdith_MindMap.json", "application/json")
