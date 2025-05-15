from typing import Optional, List, Union, Tuple
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
)
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_together import ChatTogether
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai.chat_models.base import BaseChatOpenAI

from dotenv import load_dotenv

load_dotenv()


class UnstructuredRelation(BaseModel):
    head: str = Field(
        description=(
            "extracted head entity like Microsoft, Apple, John. "
            "Must use human-readable unique identifier."
        )
    )
    head_type: str = Field(
        description="type of the extracted head entity like Person, Company, etc"
    )
    relation: str = Field(description="relation between the head and the tail entities")
    relation_properties: str = Field(description="the properties of relation")
    tail: str = Field(
        description=(
            "extracted tail entity like Microsoft, Apple, John. "
            "Must use human-readable unique identifier."
        )
    )
    tail_type: str = Field(
        description="type of the extracted tail entity like Person, Company, etc"
    )


class LLMGraphTransformer:
    """
    Wrapper of LLM model enables it to extract nodes and relations from a given text under graph form.
    This code is refered from Langchain's LLM Graph Transformer code
    https://github.com/langchain-ai/langchain-experimental/blob/main/libs/experimental/langchain_experimental/graph_transformers/llm.py
    with major improvements:
    - Support with any LLMs model, not only structured output support models like properietary models: GPT-4, Claude-3, Gemini-2
    - Add more data into relation, head and tail nodes under properties.
    """

    def __init__(self, llm=Union[ChatTogether, BaseLanguageModel, BaseChatOpenAI]):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=UnstructuredRelation)
        self.examples = [
            {
                "text": (
                    "Adam is a software engineer in Microsoft since 2009, "
                    "and last year he got an award as the Best Talent"
                ),
                "head": "Adam",
                "head_type": "Person",
                "relation": "WORKS_FOR",
                "relation_properties": "since 2009",
                "tail": "Microsoft",
                "tail_type": "Company",
            },
            {
                "text": (
                    "Adam is a software engineer in Microsoft since 2009, "
                    "and last year he got an award as the Best Talent"
                ),
                "head": "Adam",
                "head_type": "Person",
                "relation": "HAS_AWARD",
                "relation_properties": "last year",
                "tail": "Best Talent",
                "tail_type": "Award",
            },
            {
                "text": (
                    "Microsoft is a tech company that provide "
                    "several products such as Microsoft Word"
                ),
                "head": "Microsoft Word",
                "head_type": "Product",
                "relation": "PRODUCED_BY",
                "relation_properties": "",
                "tail": "Microsoft",
                "tail_type": "Company",
            },
            {
                "text": "Microsoft Word is a lightweight app that accessible offline",
                "head": "Microsoft Word",
                "head_type": "Product",
                "relation": "HAS_CHARACTERISTIC",
                "relation_properties": "accessible offline",
                "tail": "lightweight app",
                "tail_type": "Characteristic",
            },
            {
                "text": "Microsoft Word is a lightweight app that accessible offline",
                "head": "Microsoft Word",
                "head_type": "Product",
                "relation": "HAS_CHARACTERISTIC",
                "relation_properties": "accessible offline",
                "tail": "accessible offline",
                "tail_type": "Characteristic",
            },
        ]

    def create_unstructured_prompt(
        self,
        node_labels: Optional[List[str]] = None,
        rel_types: Optional[Union[List[str], List[Tuple[str, str, str]]]] = None,
        relationship_type: Optional[str] = None,
        additional_instructions: Optional[str] = "",
    ) -> ChatPromptTemplate:
        """
        Create a prompt template for extracting information from a text using a graph.
        The prompt template includes instructions for identifying nodes and relationships
        in the text, and the user can specify the types of nodes and relationships to
        extract.

        Args:
            - node_labels (Optional[List[str]]): A list of valid entity types to be used as node labels in the extracted relationships (e.g., ["Person", "Organization"]).
            - rel_types (Optional[Union[List[str], List[Tuple[str, str, str]]]]): A list of valid relationship types. Can be either simple strings (e.g., ["works_for", "founded_by"]) or structured triplets like (head_type, relation, tail_type) if relationship_type="tuple".
            - relationship_type (Optional[str]): Indicates how rel_types should be interpreted. If "tuple", the function extracts the relation from the second element of each triplet.
            - additional_instructions (Optional[str]): Any extra instructions you want to include in the system or human prompts.
        Returns:
            ChatPromptTemplate: A prompt template for extracting information from a text using a graph.
        """

        node_labels_str = str(node_labels) if node_labels else ""
        if rel_types:
            if relationship_type == "tuple":
                rel_types_str = str(list({item[1] for item in rel_types}))
            else:
                rel_types_str = str(rel_types)
        else:
            rel_types_str = ""
        base_string_parts = [
            "You are a top-tier algorithm designed for extracting information in "
            "structured formats to build a knowledge graph. Your task is to identify "
            "the entities and relations requested with the user prompt from a given "
            "text. You must generate the output in a JSON format containing a list "
            'with JSON objects. Each object should have the keys: "head", '
            '"head_type", "relation", "tail", and "tail_type". The "head" '
            "key must contain the text of the extracted entity with one of the types "
            "from the provided list in the user prompt.",
            f'The "head_type" key must contain the type of the extracted head entity, '
            f"which must be one of the types from {node_labels_str}."
            if node_labels
            else "",
            f'The "relation" key must contain the type of relation between the "head" '
            f'and the "tail", which must be one of the relations from {rel_types_str}.'
            if rel_types
            else "",
            f'The "tail" key must represent the text of an extracted entity which is '
            f'the tail of the relation, and the "tail_type" key must contain the type '
            f"of the tail entity from {node_labels_str}."
            if node_labels
            else "",
            "Your task is to extract relationships from text strictly adhering "
            "to the provided schema. The relationships can only appear "
            "between specific node types are presented in the schema format "
            "like: (Entity1Type, RELATIONSHIP_TYPE, Entity2Type) /n"
            f"Provided schema is {rel_types}"
            if relationship_type == "tuple"
            else "",
            "Attempt to extract as many entities and relations as you can. Maintain "
            "Entity Consistency: When extracting entities, it's vital to ensure "
            'consistency. If an entity, such as "John Doe", is mentioned multiple '
            "times in the text but is referred to by different names or pronouns "
            '(e.g., "Joe", "he"), always use the most complete identifier for '
            "that entity. The knowledge graph should be coherent and easily "
            "understandable, so maintaining consistency in entity references is "
            "crucial.",
            "IMPORTANT NOTES:\n- Don't add any explanation and text. ",
            additional_instructions,
        ]
        system_prompt = "\n".join(filter(None, base_string_parts))

        system_message = SystemMessage(content=system_prompt)
        parser = JsonOutputParser(pydantic_object=UnstructuredRelation)

        human_string_parts = [
            "Based on the following example, extract entities and "
            "relations from the provided text.\n\n",
            "Use the following entity types, don't use other entity "
            "that is not defined below:"
            "# ENTITY TYPES:"
            "{node_labels}"
            if node_labels
            else "",
            "Use the following relation types, don't use other relation "
            "that is not defined below:"
            "# RELATION TYPES:"
            "{rel_types}"
            if rel_types
            else "",
            "Your task is to extract relationships from text strictly adhering "
            "to the provided schema. The relationships can only appear "
            "between specific node types are presented in the schema format "
            "like: (Entity1Type, RELATIONSHIP_TYPE, Entity2Type) /n"
            f"Provided schema is {rel_types}"
            if relationship_type == "tuple"
            else "",
            "Below are a number of examples of text and their extracted "
            "entities and relationships."
            "{examples}\n",
            additional_instructions,
            "For the following text, extract entities and relations as "
            "in the provided example."
            "{format_instructions}\nText: {input}",
        ]
        human_prompt_string = "\n".join(filter(None, human_string_parts))
        human_prompt = PromptTemplate(
            template=human_prompt_string,
            input_variables=["input"],
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
                "node_labels": node_labels,
                "rel_types": rel_types,
                "examples": self.examples,
            },
        )

        human_message_prompt = HumanMessagePromptTemplate(prompt=human_prompt)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message, human_message_prompt]
        )
        return chat_prompt

    def generate_graph(
        self,
        message: str,
        node_labels: Optional[List[str]] = None,
        rel_types: Optional[Union[List[str], List[Tuple[str, str, str]]]] = None,
        relationship_type: Optional[str] = None,
        additional_instructions: Optional[str] = "",
    ):
        prompt = self.create_unstructured_prompt(
            node_labels=node_labels,
            rel_types=rel_types,
            relationship_type=relationship_type,
            additional_instructions=additional_instructions,
        )

        self.chain = prompt | self.llm | self.parser
        extracted_content = self.chain.invoke(message)
        return extracted_content
