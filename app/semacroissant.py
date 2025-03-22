import os
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import uvicorn
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(
    title="RDF Graph Query API",
    description="API for querying RDF data from Semantic MediaWiki",
    version="1.0.0"
)

# Global variables to store the graph and namespaces
graph = None
SWIVT = None
PROPERTY = None
WIKI = None

class QueryResult(BaseModel):
    subject: str
    properties: Dict[str, Any]

class GraphStats(BaseModel):
    triples: int
    subjects: int
    predicates: int
    objects: int

class EndpointInfo(BaseModel):
    description: str

class RootResponse(BaseModel):
    name: str
    version: str
    description: str
    endpoints: Dict[str, str]

def clean_property_name(prop_uri):
    """
    Clean property URIs by removing 'Property-3A' and '-23aux' suffixes.
    
    Args:
        prop_uri (URIRef): The property URI to clean
        
    Returns:
        str: Cleaned property name
    """
    prop_str = str(prop_uri)
    
    # Extract the property name from the URI
    prop_name = prop_str.split('/')[-1]
    
    # Remove 'Property-3A' prefix if present
    if 'Property-3A' in prop_name:
        prop_name = prop_name.replace('Property-3A', '')
    
    # Remove '-23aux' suffix if present
    if '-23aux' in prop_name:
        prop_name = prop_name.replace('-23aux', '')

    if 'http://kb.dansdemo.nl/' in prop_name:
        prop_name = prop_name.replace('http://kb.dansdemo.nl/', '/')
    
    return prop_name

def clean_uri_or_property(uri):
    """
    Clean the URI or property by removing repeated segments.
    
    Args:
        uri (str): The URI or property to clean
        
    Returns:
        str: Cleaned URI or property
    """
    if 'file://' in uri:
        uri = uri.replace('file://', '')
    # Remove repeated segments by using a set to keep unique parts
    parts = uri.split('/')
    cleaned_parts = []
    seen = set()
    
    for part in parts:
        if part not in seen:
            cleaned_parts.append(part)
            seen.add(part)
    
    return '/'.join(cleaned_parts)

def clean_object(obj):
    if isinstance(obj, Literal):
        return str(obj)
    elif isinstance(obj, URIRef):
        if 'http://kb.dansdemo.nl/' in str(obj):
            return str(obj).replace('http://kb.dansdemo.nl/', '/')
        else:
            return clean_uri_or_property(str(obj))
    else:
        return str(obj)

def extract_properties(g, subject_uri):
    """
    Extract all properties from the graph with cleaned names for a specific subject.
    
    Args:
        g (Graph): RDF graph
        subject_uri (URIRef): Subject URI
        
    Returns:
        dict: Dictionary of cleaned property names and values
    """
    properties = {}
    
    # Extract all properties for the subject
    for pred, obj in g.predicate_objects(subject_uri):
        # Clean the property name
        clean_pred = clean_property_name(pred)
        
        # Format the object value
        if isinstance(obj, Literal):
            obj_value = str(obj)
        elif isinstance(obj, URIRef):
            obj_value = clean_uri_or_property(str(obj))  # Clean the URI or property
        else:
            obj_value = str(obj)
        
        # Add to properties dictionary, avoiding duplicates
        if clean_pred in properties:
            # If property already exists, convert to list or append to existing list
            if isinstance(properties[clean_pred], list):
                if obj_value not in properties[clean_pred]:  # Check for duplicates
                    properties[clean_pred].append(obj_value)
            else:
                if properties[clean_pred] != obj_value:  # Check for duplicates
                    properties[clean_pred] = [properties[clean_pred], obj_value]
        else:
            properties[clean_pred] = obj_value
    
    return properties

def load_rdf_graph(file_path):
    """
    Load RDF data from a file.
    
    Args:
        file_path (str): Path to the RDF file
        
    Returns:
        tuple: (Graph, SWIVT, PROPERTY, WIKI) - the graph and namespace objects
    """
    global graph, SWIVT, PROPERTY, WIKI
    if not '/' in file_path:
        try:
            file_path = os.environ.get("DATA_DIR") + "/" + file_path
        except Exception as e:
            #raise Exception(f"Error getting DATA_DIR: {e}")
            print("Something went wrong with getting DATA_DIR")
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
    
    # Create a new RDF Graph
    g = Graph()
    
    try:
        # Parse the RDF file
        g.parse(file_path, format="xml")
        print(f"Successfully parsed RDF file: {file_path}")
        print(f"Graph contains {len(g)} triples")
    except Exception as e:
        raise Exception(f"Error parsing RDF file: {e}")
    
    # Define namespaces for easier querying
    SWIVT = Namespace("http://semantic-mediawiki.org/swivt/1.0#")
    PROPERTY = Namespace("http://kb/Property:")
    WIKI = Namespace("http://kb/")
    
    # Bind namespaces to prefixes for more readable output
    g.bind("swivt", SWIVT)
    g.bind("property", PROPERTY)
    g.bind("wiki", WIKI)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    
    # Store in global variables
    graph = g
    
    return g, SWIVT, PROPERTY, WIKI

def serialize_graph(file_path):
    """
    Serialize the RDF graph to a file in Turtle format.
    
    Args:
        file_path (str): Path to the output file
    """
    global graph
    
    if graph is None:
        raise Exception("No graph loaded. Please load a graph before serialization.")
    
    # Serialize the graph to Turtle format
    graph.serialize(destination=file_path, format='turtle')
    print(f"Graph serialized to {file_path}")

@app.get("/", response_model=RootResponse)
async def read_root():
    return {
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

@app.post("/load", response_model=GraphStats)
async def load_graph(file_path: str):
    """
    Load an RDF graph from a file.
    
    Args:
        file_path (str): Path to the RDF file
        
    Returns:
        GraphStats: Statistics about the loaded graph
    """
    try:
        global graph, SWIVT, PROPERTY, WIKI
        graph, SWIVT, PROPERTY, WIKI = load_rdf_graph(file_path)
        
        # Serialize the graph to dynamic_graph.ttl
        try:
            serialize_graph(os.environ.get("DATA_DIR") + "/dynamic_graph.ttl")
        except Exception as e:
            serialize_graph("../data/dynamic_graph.ttl")

        
        # Count unique subjects, predicates, and objects
        subjects = set(graph.subjects())
        predicates = set(graph.predicates())
        objects = set(graph.objects())
        
        return {
            "triples": len(graph),
            "subjects": len(subjects),
            "predicates": len(predicates),
            "objects": len(objects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=GraphStats)
async def get_stats():
    """
    Get statistics about the loaded graph.
    
    Returns:
        GraphStats: Statistics about the loaded graph
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    # Count unique subjects, predicates, and objects
    subjects = set(graph.subjects())
    predicates = set(graph.predicates())
    objects = set(graph.objects())
    
    return {
        "triples": len(graph),
        "subjects": len(subjects),
        "predicates": len(predicates),
        "objects": len(objects)
    }

@app.get("/subjects", response_model=List[Dict[str, str]])
async def get_subjects(limit: int = 100, offset: int = 0):
    """
    Get a list of subjects in the graph.
    
    Args:
        limit (int): Maximum number of subjects to return
        offset (int): Number of subjects to skip
        
    Returns:
        List[Dict[str, str]]: List of subjects with their labels
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    subjects = []
    
    # Get all subjects
    all_subjects = list(set(graph.subjects()))
    
    # Apply pagination
    paginated_subjects = all_subjects[offset:offset+limit]
    
    for subject in paginated_subjects:
        # Get the label if available
        label = None
        for o in graph.objects(subject, RDFS.label):
            label = str(o)
            break
        
        subjects.append({
            "uri": str(subject),
            "label": label if label else str(subject).split('/')[-1]
        })
    
    return subjects

@app.get("/subject/{subject_id}", response_model=QueryResult)
async def get_subject(subject_id: str):
    """
    Get details about a specific subject.
    
    Args:
        subject_id (str): Subject ID or URI
        
    Returns:
        QueryResult: Subject details with properties
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    # Try to find the subject
    subject_uri = None
    
    # If subject_id is a full URI
    if subject_id.startswith('http://') or subject_id.startswith('https://'):
        subject_uri = URIRef(subject_id)
    else:
        # Try to find by label
        for s, p, o in graph.triples((None, RDFS.label, Literal(subject_id))):
            subject_uri = s
            break
        
        # If not found by label, try as a local name
        if subject_uri is None:
            for s in graph.subjects():
                if str(s).split('/')[-1] == subject_id:
                    subject_uri = s
                    break
    
    if subject_uri is None:
        raise HTTPException(status_code=404, detail=f"Subject '{subject_id}' not found")
    
    # Extract properties
    properties = extract_properties(graph, subject_uri)
    
    return {
        "subject": str(subject_uri),
        "properties": properties
    }

@app.get("/search", response_model=List[Dict[str, str]])
async def search_subjects(q: str, limit: int = 100):
    """
    Search for subjects by label.
    
    Args:
        q (str): Search query
        limit (int): Maximum number of results to return
        
    Returns:
        List[Dict[str, str]]: List of matching subjects
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    results = []
    count = 0
    
    # Search by label
    for s, p, o in graph.triples((None, RDFS.label, None)):
        label = str(o)
        if q.lower() in label.lower():
            results.append({
                "uri": str(s),
                "label": label
            })
            count += 1
            if count >= limit:
                break
    
    return results

@app.post("/sparql", response_model=List[Dict[str, Any]])
async def execute_sparql(query: Dict[str, Any]):
    """
    Execute a SPARQL query on the graph.
    
    Args:
        query (str): SPARQL query
        
    Returns:
        List[Dict[str, Any]]: Query results
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    try:
        sparql_query = query.get("query")
        if not sparql_query:
            raise HTTPException(status_code=400, detail="Query parameter 'query' is required.")
        results = graph.query(sparql_query)
        # Convert results to a list of dictionaries
        formatted_results = [{str(var): str(row[var]) for var in results.vars} for row in results]
        
        print(formatted_results)  # Optional: Print the formatted results for debugging
        return formatted_results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SPARQL query error: {str(e)}")

@app.get("/properties", response_model=List[str])
async def get_properties():
    """
    Get a list of all properties in the graph.
    
    Returns:
        List[str]: List of property names
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    properties = set()
    
    for p in graph.predicates():
        clean_prop = clean_property_name(p)
        properties.add(clean_prop)
    
    return sorted(list(properties))

@app.get("/property/{property_name}", response_model=List[Dict[str, str]])
async def get_property_values(property_name: str, limit: int = 100, offset: int = 0):
    """
    Get subjects and values for a specific property.
    
    Args:
        property_name (str): Property name
        limit (int): Maximum number of results to return
        offset (int): Number of results to skip
        
    Returns:
        List[Dict[str, str]]: List of subjects and values
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    results = []
    count = 0
    
    # Find all predicates that match the cleaned property name
    matching_predicates = []
    for p in graph.predicates():
        if clean_property_name(p) == property_name:
            matching_predicates.append(p)
    
    if not matching_predicates:
        raise HTTPException(status_code=404, detail=f"Property '{property_name}' not found")
    
    # Get all subject-object pairs for the matching predicates
    all_pairs = []
    for pred in matching_predicates:
        for s, o in graph.subject_objects(pred):
            all_pairs.append((s, o))
    
    # Apply pagination
    paginated_pairs = all_pairs[offset:offset+limit]
    
    for s, o in paginated_pairs:
        # Get the subject label if available
        subject_label = None
        for label in graph.objects(s, RDFS.label):
            subject_label = str(label)
            break
        
        # Format the object value
        if isinstance(o, Literal):
            obj_value = str(o)
        elif isinstance(o, URIRef):
            obj_value = clean_object(o)
        else:
            obj_value = str(o)
        
        results.append({
            "subject_uri": str(s),
            "subject_label": subject_label if subject_label else str(s).split('/')[-1],
            "value": obj_value
        })
    
    return results

@app.get("/unique_subjects", response_model=List[str])
async def get_unique_subjects():
    """
    Get a list of all unique subjects in the graph.
    
    Returns:
        List[str]: List of unique subject URIs
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    # Get all unique subjects
    unique_subjects = list(set(graph.subjects()))
    
    # Convert subjects to string format
    return [str(subject) for subject in unique_subjects]

@app.get("/unique_objects", response_model=List[str])
async def get_unique_objects():
    """
    Get a list of all unique objects in the graph.
    
    Returns:
        List[str]: List of unique object URIs
    """
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Use /load endpoint first.")
    
    # Get all unique objects
    unique_objects = set()
    
    # Iterate through all predicates and their corresponding objects
    for pred, obj in graph.predicate_objects():
        obj = clean_object(obj)
        unique_objects.add(str(obj))  # Only add the object to the set
    
    return sorted(list(unique_objects))

def start_server():
    """Start the FastAPI server."""
    uvicorn.run("semacroissant:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
