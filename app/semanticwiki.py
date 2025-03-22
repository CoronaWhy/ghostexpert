import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import os
import re

def parse_rdf_file(file_path):
    """
    Parse RDF data from a file.
    
    Args:
        file_path (str): Path to the RDF file
        
    Returns:
        tuple: (Graph, SWIVT, PROPERTY, WIKI) - the graph and namespace objects
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None
    
    # Create a new RDF Graph
    g = Graph()
    
    try:
        # Parse the RDF file
        g.parse(file_path, format="xml")
        print(f"Successfully parsed RDF file: {file_path}")
        print(f"Graph contains {len(g)} triples")
    except Exception as e:
        print(f"Error parsing RDF file: {e}")
        return None
    
    # Define namespaces for easier querying
    SWIVT = Namespace("http://semantic-mediawiki.org/swivt/1.0#")
    PROPERTY = Namespace("http://kb.dansdemo.nl/Property:")
    WIKI = Namespace("http://kb.dansdemo.nl/")
    
    # Bind namespaces to prefixes for more readable output
    g.bind("swivt", SWIVT)
    g.bind("property", PROPERTY)
    g.bind("wiki", WIKI)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    
    return g, SWIVT, PROPERTY, WIKI

def clean_property_name(prop_uri):
    """
    Clean property URIs by removing 'Property-3A' and '-23aux' suffixes.
    
    Args:
        prop_uri (URIRef): The property URI to clean
        
    Returns:
        str: Cleaned property URI
    """
    return re.sub(r'-3A$|-23aux$', '', str(prop_uri))

def analyze_odissei_data(g, SWIVT, PROPERTY, WIKI):
    """
    Analyze and display information about the ODISSEI project from the RDF graph.
    
    Args:
        g (Graph): RDF graph containing the ODISSEI data
        SWIVT, PROPERTY, WIKI: Namespace objects
    """
    if g is None or len(g) == 0:
        print("No data to analyze.")
        return
    
    # Get the subject URI
    # First try to find the ODISSEI subject
    subject_uri = None
    for s, p, o in g.triples((None, RDFS.label, Literal("ODISSEI"))):
        subject_uri = s
        break
    
    # If not found, try to find any subject
    if subject_uri is None:
        for s in g.subjects():
            subject_uri = s
            break
    
    if subject_uri is None:
        print("Could not find the ODISSEI subject in the RDF data.")
        return
    
    print(f"\n=== ODISSEI Project Information ({subject_uri}) ===\n")
    
    # Get basic information
    print("Basic Information:")
    print("-" * 50)
    
    # Get the label
    labels = list(g.objects(subject_uri, RDFS.label))
    if labels:
        for label in labels:
            print(f"Name: {label}")
    else:
        print("Name: Not specified")
    
    # Get the type
    types = list(g.objects(subject_uri, RDF.type))
    if types:
        for type_uri in types:
            print(f"Type: {type_uri}")
    else:
        print("Type: Not specified")
    
    # Get the description
    descriptions = list(g.objects(subject_uri, PROPERTY.description))
    if descriptions:
        for desc in descriptions:
            print(f"\nDescription: {desc}")
    else:
        print("\nDescription: Not specified")
    
    # Get dates
    print("\nDates:")
    print("-" * 50)
    
    creation_dates = list(g.objects(subject_uri, SWIVT.wikiPageCreationDate))
    if creation_dates:
        for date in creation_dates:
            print(f"Creation Date: {date}")
    else:
        print("Creation Date: Not specified")
    
    mod_dates = list(g.objects(subject_uri, SWIVT.wikiPageModificationDate))
    if mod_dates:
        for date in mod_dates:
            print(f"Last Modified: {date}")
    else:
        print("Last Modified: Not specified")
    
    end_dates = list(g.objects(subject_uri, PROPERTY.endDate))
    if end_dates:
        for date in end_dates:
            print(f"End Date: {date}")
    else:
        print("End Date: Not specified")
    
    # Get participants
    print("\nParticipants:")
    print("-" * 50)
    
    participants = list(g.objects(subject_uri, PROPERTY.participant))
    if participants:
        for participant in participants:
            print(f"- {participant}")
    else:
        print("No participants specified")
    
    # Get other properties
    print("\nOther Properties:")
    print("-" * 50)
    
    geo_scopes = list(g.objects(subject_uri, PROPERTY.geographicScope))
    if geo_scopes:
        for scope in geo_scopes:
            print(f"Geographic Scope: {scope}")
    else:
        print("Geographic Scope: Not specified")
    
    repos = list(g.objects(subject_uri, PROPERTY.hasRepository))
    if repos:
        for repo in repos:
            print(f"Repository: {repo}")
    else:
        print("Repository: Not specified")
    
    institutions = list(g.objects(subject_uri, PROPERTY.partnerInstitution))
    if institutions:
        for institution in institutions:
            print(f"Partner Institution: {institution}")
    else:
        print("Partner Institution: Not specified")
    
    editors = list(g.objects(subject_uri, PROPERTY.Last_editor_is))
    if editors:
        for editor in editors:
            print(f"Last Editor: {editor}")
    else:
        print("Last Editor: Not specified")
    
    # Print all properties with cleaned names
    print("\n=== All Properties (Cleaned) ===")
    print("-" * 50)
    
    for pred, obj in g.predicate_objects(subject_uri):
        # Clean the property name
        clean_pred = clean_property_name(pred)
        
        # Format the object value
        if isinstance(obj, Literal):
            obj_value = obj
        elif isinstance(obj, URIRef):
            obj_value = f"<{obj}>"
        else:
            obj_value = str(obj)
        
        print(f"{clean_pred}: {obj_value}")

def run_sparql_query(graph):
    """
    Run a SPARQL query on the graph to extract specific information.
    
    Args:
        graph (Graph): RDF graph to query
    """
    if graph is None or len(graph) == 0:
        print("No data to query.")
        return
    
    print("\n=== SPARQL Query Results ===")
    print("-" * 50)
    
    # Example SPARQL query to get project details
    query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX swivt: <http://semantic-mediawiki.org/swivt/1.0#>
    PREFIX property: <http://kb.dansdemo.nl/Property:>
    
    SELECT ?subject ?name ?description ?endDate ?geographicScope ?repository
    WHERE {
        ?subject rdfs:label ?name .
        OPTIONAL { ?subject property:description ?description . }
        OPTIONAL { ?subject property:endDate ?endDate . }
        OPTIONAL { ?subject property:geographicScope ?geographicScope . }
        OPTIONAL { ?subject property:hasRepository ?repository . }
    }
    """
    
    results = graph.query(query)
    
    if not results:
        print("No results found for the query.")
        return
    
    for row in results:
        print(f"Subject: {row.subject}")
        print(f"Project Name: {row.name}")
        if hasattr(row, 'description') and row.description:
            print(f"Description: {row.description}")
        if hasattr(row, 'endDate') and row.endDate:
            print(f"End Date: {row.endDate}")
        if hasattr(row, 'geographicScope') and row.geographicScope:
            print(f"Geographic Scope: {row.geographicScope}")
        if hasattr(row, 'repository') and row.repository:
            print(f"Repository: {row.repository}")
    
    # Query to get all participants
    participant_query = """
    PREFIX property: <http://kb.dansdemo.nl/Property:>
    
    SELECT ?subject ?participant
    WHERE {
        ?subject property:participant ?participant .
    }
    """
    
    participant_results = graph.query(participant_query)
    
    if participant_results:
        print("\nParticipants:")
        for row in participant_results:
            print(f"Subject: {row.subject}")
            print(f"- {row.participant}")
    else:
        print("\nNo participants found.")

def save_to_formats(graph, base_filename="odissei_project"):
    """
    Save the RDF graph to different formats.
    
    Args:
        graph (Graph): RDF graph to save
        base_filename (str): Base filename for the output files
    """
    if graph is None or len(graph) == 0:
        print("No data to save.")
        return
    
    try:
        # Save as Turtle
        turtle_data = graph.serialize(format="turtle")
        with open(f"{base_filename}.ttl", "w", encoding="utf-8") as f:
            f.write(turtle_data)
        
        # Save as JSON-LD
        jsonld_data = graph.serialize(format="json-ld")
        with open(f"{base_filename}.jsonld", "w", encoding="utf-8") as f:
            f.write(jsonld_data)
        
        # Save as N-Triples
        nt_data = graph.serialize(format="nt")
        with open(f"{base_filename}.nt", "w", encoding="utf-8") as f:
            f.write(nt_data)
        
        print(f"\nRDF data saved in Turtle, JSON-LD, and N-Triples formats with base filename '{base_filename}'.")
    except Exception as e:
        print(f"Error saving RDF data: {e}")

def main():
    # Get the file path from the user
    file_path = input("Enter the path to the RDF file: ")
    
    # Parse the RDF file
    result = parse_rdf_file(file_path)
    
    if result:
        graph, SWIVT, PROPERTY, WIKI = result
        
        # Analyze the data
        analyze_odissei_data(graph, SWIVT, PROPERTY, WIKI)
        
        # Run SPARQL queries
        run_sparql_query(graph)
        
        # Ask if the user wants to save the data
        save_option = input("\nDo you want to save the RDF data in different formats? (y/n): ")
        if save_option.lower() == 'y':
            base_filename = input("Enter base filename for output files (default: odissei_project): ")
            if not base_filename:
                base_filename = "odissei_project"
            save_to_formats(graph, base_filename)

if __name__ == "__main__":
    main()
