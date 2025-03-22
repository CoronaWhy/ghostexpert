import sys
import os
from fastapi.testclient import TestClient
import pytest

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from semacroissant import app  # Now this should work

# Initialize the test client
client = TestClient(app)

# Load the dynamic_graph.ttl file for testing
@pytest.fixture(scope="module", autouse=True)
def load_graph():
    test_file_path = "/Users/vyacheslavtykhonov/projects/ghostexpert/data/DANS-KB-wiki-20250303-dump.rdf"  # Adjust this path as necessary
    #test_file_path = "/data/DANS-KB-wiki-20250303-dump.rdf"  # Adjust this path as necessary
    assert os.path.exists(test_file_path), f"Test file {test_file_path} does not exist."

    # Load the RDF graph with the Accept header set to application/xml
    response = client.post(
        "/load",
        params={"file_path": test_file_path},  # Use params to send query parameters
        headers={"Accept": "application/xml"}  # Changed to application/xml
    )
    assert response.status_code == 200, f"Failed to load graph: {response.content}"  # Print response content for debugging

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "RDF Graph Query API",
        "version": "1.0.0",
        "description": "API for querying RDF data from Semantic MediaWiki",
        "endpoints": {
            "/load": "Load RDF data from a file",
            "/stats": "Get statistics about the loaded graph",
            "/unique_subjects": "Get a list of all unique subjects in the graph.",
            "/unique_objects": "Get a list of all unique objects in the graph.",
            "/search": "Search for subjects by label",
            "/sparql": "Execute a SPARQL query on the graph"
        }
    }

def test_get_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    assert "triples" in response.json()
    assert "subjects" in response.json()
    assert "predicates" in response.json()
    assert "objects" in response.json()

def test_get_unique_subjects():
    response = client.get("/unique_subjects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_unique_objects():
    response = client.get("/unique_objects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_subject():
    # Replace 'some_subject_id' with an actual subject ID from your graph
    response = client.get("/subject/website")
    assert response.status_code == 200
    assert "subject" in response.json()
    assert "properties" in response.json()

def test_search_subjects():
    response = client.get("/search?q=ODISSEI")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_execute_sparql():
    # Replace 'SELECT ?s WHERE { ?s ?p ?o }' with a valid SPARQL query for your graph
    response = client.post("/sparql", json={"query": "SELECT ?s WHERE { ?s ?p ?o }"})
    assert response.status_code == 200
    assert isinstance(response.json(), list) 