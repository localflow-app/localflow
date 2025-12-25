import sys
from pathlib import Path
import shutil

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.workflow_executor import WorkflowExecutor
from src.core.node_base import VariableAssignNode, VariableCalcNode, NodeType

def test_optimization():
    print("Testing optimization...")
    workflow_name = "test_opt_workflow"
    
    # Init executor
    executor = WorkflowExecutor(workflow_name)
    
    # Create nodes
    node1 = VariableAssignNode(
        node_id="node1",
        config={"variable_name": "a", "value": "10", "value_type": "int"}
    )
    
    node2 = VariableCalcNode(
        node_id="node2",
        config={"expression": "a * 2", "output_var": "result"}
    )
    
    # Add nodes and edge
    executor.add_node(node1)
    executor.add_node(node2)
    executor.add_edge("node1", "node2")
    
    # Prepare env
    print("Preparing environment...")
    executor.prepare_environment(python_version="3.10")
    
    # Execute
    print("Executing workflow...")
    import time
    start = time.time()
    result = executor.execute()
    end = time.time()
    
    print(f"Execution took {end - start:.2f} seconds")
    print(f"Result: {result}")
    
    assert result.get("a") == 10
    assert result.get("result") == 20
    print("Verification Passed!")

if __name__ == "__main__":
    test_optimization()
