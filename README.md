# Intelligent Agent powered by Artificial Intelligence

This agent is designed to navigate the Web (Web 2.0), intelligently process information and execute some actions in the autonomous mode.

## Intro

Run any prompt and Intelligent Agent will run some actions and give you requested information back. 

Example:
"I am searching for the most recent news or updates related to ChatGPT."

Expected result is RSS feed like this and it can be shared with other people by Decentralized Identifiers called DIDs:
```
<?xml version="1.0" encoding="UTF-8"?>
  <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <channel>
      <title>chatgpt</title>
      <link>https://now.museum</link>
      <description>Now.Museum feed on chatgpt</description>
      <language>en-US</language>
      <generator>rfeed v1.1.1</generator>
      <item>
        <title>Winner of Japan's top literary prize used ChatGPT</title>
        <link>http://www.thenationalnews.com/arts-culture/books/2024/01/20/japan-chatgpt-author-winner/</link>
        <description> Rie Kudan tasked internet bot to help write 5 per cent of novel Rie Kudan's book Tokyo-to Dojo-to (Tokyo Sympathy Tower) won the Akutagawa Prize. Photo: The Yomiuri Shimbun Powered by automated translation A Japanese author won the country’s top literary prize – then admitted to using ChatGPT to write a portion of the book.</description>
        <author>thenationalnews.com</author>
        <guid isPermaLink="true">http://www.thenationalnews.com/arts-culture/books/2024/01/20/japan-chatgpt-author-winner/</guid>
      </item>
      ...
```

## Features

* Information Harvesting: The agent is capable of autonomously collecting relevant data from various sources on the Web.

* Natural Language Processing (NLP): It performs processing on the acquired information to extract named entities and other concepts using natural language processing techniques.

* Ontology Integration: The agent integrates extracted information with established ontologies such as SKOS (Simple Knowledge Organization System), OWL (Web Ontology Language), and other relevant ontologies.

* Relationship Building: Using the integrated ontologies, the agent builds relationships between extracted concepts, enhancing the semantic understanding of the collected information.

In summary, it's a sophisticated agent that combines web harvesting, natural language processing, and ontology-based semantic modeling to extract meaningful concepts and relationships from the Web, and build global Knowledge Graph. This type of agent is valuable for knowledge discovery, semantic annotation, and building a structured representation of information for further analysis or use in intelligent systems.

## Role of Decentralized Identifiers (DIDs) in the Intelligent Agent:

### Identity Verification:

DIDs can be utilized to uniquely identify entities, such as users, data sources, or other agents involved in the information extraction process.
The decentralized nature of DIDs ensures that identities are self-owned and controlled, enhancing security and privacy.
### Secure Data Sources:

DIDs can be associated with data sources, ensuring that the agent extracts information from verified and trusted origins.
This helps in mitigating the risk of tampered or malicious data.
### Linked Data Integrity:

DIDs can be embedded in the semantic model or linked data to establish a secure and tamper-evident connection between entities.
This enhances the integrity of relationships and concepts within the semantic graph.
### Interoperability:

DIDs facilitate interoperability by providing a standardized method for identity representation and verification across different systems and platforms.
The agent can interact with other agents or systems that recognize and trust DIDs.
### User Control:

Users interacting with the agent may have DIDs representing their identities, allowing them to control and manage access to their personal information during the extraction process.
By incorporating DIDs into the system, the semantic web agent gains a robust identity framework that contributes to the overall security, trustworthiness, and user-centricity of the information extraction and relationship building process.






