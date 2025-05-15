import os
import json
import logging
from typing import Union, Optional, Tuple, List
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from aucodb.graph.llm_graph_transformer import LLMGraphTransformer
from pyvis.network import Network
import webbrowser

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AucoDBNeo4jClient:
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        assert self.uri, "Must have uri connection"
        assert self.user, "Must have username and password to login"
        assert self.password, "Must have username and password to login"
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def clear_database(self) -> None:
        """Clear all nodes and relationships in the database."""
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("Database cleared successfully")
        except Neo4jError as e:
            logger.error(f"Failed to clear database: {e}")
            raise

    def validate_route(self, route: dict):
        """Validate that a route contains all required fields."""
        required_fields = [
            "head",
            "head_type",
            "relation",
            "relation_properties",
            "tail",
            "tail_type",
        ]
        missing_keys = required_fields - route.keys()
        if missing_keys:
            logger.error(f"Validation failed: Missing fields in item: {route}")
            raise
        return True

    def insert_graph(self, data: List[dict]) -> int:
        """
        Insert validated graph data into Neo4j.
        Returns the number of successfully inserted items.
        """
        if not data:
            logger.info("No data to insert")
            return 0

        try:
            with self.driver.session() as session:
                for item in data:
                    self.validate_route(item)
                    # Create head node
                    with self.driver.session() as session:
                        # Create head node
                        head_query = f"""
                        MERGE (h:{item['head_type']} {{name: $head_name}})
                        """
                        session.run(head_query, head_name=item["head"])

                        # Create tail node
                        tail_query = f"""
                        MERGE (t:{item['tail_type']} {{name: $tail_name}})
                        """
                        session.run(tail_query, tail_name=item["tail"])

                        # Create relationship
                        rel_props = {}
                        if item["relation_properties"]:
                            rel_props["property"] = item["relation_properties"]

                        rel_query = f"""
                        MATCH (h:{item['head_type']} {{name: $head_name}})
                        MATCH (t:{item['tail_type']} {{name: $tail_name}})
                        MERGE (h)-[r:{item['relation']}]->(t)
                        SET r += $rel_props
                        """
                        session.run(
                            rel_query,
                            head_name=item["head"],
                            tail_name=item["tail"],
                            rel_props=rel_props,
                        )
                logger.info(f"Inserted {len(data)} items into Neo4j")
                return len(data)
        except Neo4jError as e:
            logger.error(f"Failed to insert data into Neo4j: {e}")
            raise

    def generate_graph(
        self,
        llm: LLMGraphTransformer,
        message: str,
        node_labels: Optional[List[str]] = None,
        rel_types: Optional[Union[List[str], List[Tuple[str, str, str]]]] = None,
        relationship_type: Optional[str] = None,
        additional_instructions: Optional[str] = "",
    ):
        """Extract the list of routes from the graph, e.g., [Start Node] - Relationship -> [End Node] by llm_graph_transformer.py
        Args:
            - llm (LLMGraphTransformer): The LLMGraphTransformer instance used for generating the graph.
            - message (str): The input message to generate graph.
            - node_labels (Optional[List[str]]): A list of valid entity types to be used as node labels in the extracted relationships (e.g., ["Person", "Organization"]).
            - rel_types (Optional[Union[List[str], List[Tuple[str, str, str]]]]): A list of valid relationship types. Can be either simple strings (e.g., ["works_for", "founded_by"]) or structured triplets like (head_type, relation, tail_type) if relationship_type="tuple".
            - relationship_type (Optional[str]): Indicates how rel_types should be interpreted. If "tuple", the function extracts the relation from the second element of each triplet.
            - additional_instructions (Optional[str]): Any extra instructions you want to include in the system or human prompts.
        Returns:
            - routes: List of routes, each route is a list of nodes and relationships
        """
        routes = llm.generate_graph(
            message=message,
            node_labels=node_labels,
            rel_types=rel_types,
            relationship_type=relationship_type,
            additional_instructions=additional_instructions,
        )
        logging.info(f"Extracted routes: {routes}")
        return routes

    def construct_graph(
        self,
        llm: LLMGraphTransformer,
        message: str,
        is_reset_db: bool = False,
        node_labels: Optional[List[str]] = None,
        rel_types: Optional[Union[List[str], List[Tuple[str, str, str]]]] = None,
        relationship_type: Optional[str] = None,
        additional_instructions: Optional[str] = "",
    ):
        """Construct the graph from message and ingest into neo4j database"""
        assert isinstance(
            llm, LLMGraphTransformer
        ), "llm must be an instance of aucodb.graph.LLMGraphTransformer"
        if is_reset_db:
            self.clear_database()

        # 1. Generate graph by llm
        data = self.generate_graph(
            llm,
            message=message,
            node_labels=node_labels,
            rel_types=rel_types,
            relationship_type=relationship_type,
            additional_instructions=additional_instructions,
        )
        # 2. insert graph into neo4j
        self.insert_graph(data)
        # 3. close the connection
        self.close()

    def load_json_to_neo4j(self, json_file: str, is_reset_db: bool = False):
        """Ingest Graph from jsonline file, each line with format, e.g;
        {"head": "Steve Jobs", "head_type": "Person", "relation": "FOUNDED", "relation_properties": "in 1976", "tail": "Apple", "tail_type": "Company"}
        """
        if is_reset_db:
            self.clear_database()

        data = []
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        route = json.loads(line)
                        self.validate_route(route)
                        data.append(route)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Skipping invalid JSON line: {line.strip()} - Error: {e}"
                        )
        except FileNotFoundError:
            logger.error(f"File not found: {json_file}")
            raise
        except IOError as e:
            logger.error(f"Failed to read JSON file: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

        inserted_count = self.insert_graph(data)
        logger.info(f"Graph creation completed. Inserted {inserted_count} valid items")
        self.close()

    def visualize_graph(
        self, output_file: str = "graph.html", show_in_browser: bool = False
    ) -> None:
        """
        Visualize the Neo4j graph and save it as an HTML file using pyvis.
        Optionally display the graph in a web browser.

        Args:
            output_file (str): The file path to save the visualization (default: 'graph.html')
            show_in_browser (bool): Whether to open the visualization in a web browser (default: False)
        """
        try:
            with self.driver.session() as session:
                # Query to get all nodes and relationships
                query = """
                MATCH (n)-[r]->(m)
                RETURN n.name AS source, labels(n) AS source_labels, 
                       type(r) AS relationship, r.property AS rel_property,
                       m.name AS target, labels(m) AS target_labels
                """
                result = session.run(query)

                # Initialize pyvis network
                net = Network(
                    height="750px", width="100%", directed=True, notebook=False
                )

                # Add nodes and edges
                added_nodes = set()
                for record in result:
                    source = record["source"]
                    source_label = (
                        record["source_labels"][0]
                        if record["source_labels"]
                        else "Node"
                    )
                    target = record["target"]
                    target_label = (
                        record["target_labels"][0]
                        if record["target_labels"]
                        else "Node"
                    )
                    relationship = record["relationship"]
                    rel_property = (
                        record["rel_property"] if record["rel_property"] else ""
                    )

                    # Add source node
                    if source not in added_nodes:
                        net.add_node(
                            source,
                            label=f"{source}\n({source_label})",
                            title=source_label,
                        )
                        added_nodes.add(source)

                    # Add target node
                    if target not in added_nodes:
                        net.add_node(
                            target,
                            label=f"{target}\n({target_label})",
                            title=target_label,
                        )
                        added_nodes.add(target)

                    # Add edge
                    edge_label = (
                        f"{relationship}\n{rel_property}"
                        if rel_property
                        else relationship
                    )
                    net.add_edge(source, target, label=edge_label, title=relationship)

                # Save the visualization
                net.set_options(
                    """
                var options = {
                    "nodes": {
                        "font": {
                            "size": 14
                        },
                        "shape": "dot"
                    },
                    "edges": {
                        "font": {
                            "size": 12,
                            "align": "middle"
                        },
                        "arrows": "to"
                    },
                    "physics": {
                        "enabled": true,
                        "barnesHut": {
                            "gravitationalConstant": -2000,
                            "centralGravity": 0.3,
                            "springLength": 95
                        }
                    }
                }
                """
                )

                net.save_graph(output_file)
                logger.info(f"Graph visualization saved to {output_file}")

                # Optionally show in browser
                if show_in_browser:
                    webbrowser.open(f"file://{os.path.abspath(output_file)}")

        except Neo4jError as e:
            logger.error(f"Failed to visualize graph: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred during visualization: {e}")
            raise
