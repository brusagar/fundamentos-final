from dataclasses import dataclass
from typing import List, Dict, Set
from pathlib import Path
import json

@dataclass
class Relation:
    type: str
    target: str
    target_type: str

@dataclass
class Context:
    sentence: str
    other_entities: List[Dict[str, str]]
    relations: List[Relation]

@dataclass
class Entity:
    text: str
    type: str
    contexts: List[Context]

class EntityProcessor:
    def __init__(self, predictions_file: Path):
        self.entities: Dict[str, Entity] = {}
        self._load_and_process(predictions_file)
    
    def _load_and_process(self, predictions_file: Path) -> None:
        with open(predictions_file) as f:
            predictions = json.load(f)
            
        for pred in predictions:
            tokens = pred['tokens']
            sentence = ' '.join(tokens)
            entities = pred.get('entities', [])
            relations = pred.get('relations', [])
            
            # Map entity indices to their information
            entity_map = {}
            for idx, entity in enumerate(entities):
                text = ' '.join(tokens[entity['start']:entity['end']])
                entity_type = entity['type']
                
                if text not in self.entities:
                    self.entities[text] = Entity(text=text, type=entity_type, contexts=[])
                
                entity_map[idx] = (text, entity_type)
            
            # Process contexts and relations for each entity
            for idx, (text, _) in entity_map.items():
                # Get other entities in this sentence
                other_entities = [
                    {'text': e_text, 'type': e_type}
                    for i, (e_text, e_type) in entity_map.items()
                    if i != idx
                ]
                
                # Get relations for this entity
                entity_relations = []
                for relation in relations:
                    if relation['head'] == idx:
                        target_text, target_type = entity_map[relation['tail']]
                        entity_relations.append(Relation(
                            type=relation['type'],
                            target=target_text,
                            target_type=target_type
                        ))
                    elif relation['tail'] == idx:
                        source_text, source_type = entity_map[relation['head']]
                        entity_relations.append(Relation(
                            type=relation['type'],
                            target=source_text,
                            target_type=source_type
                        ))
                
                # Add context to entity
                self.entities[text].contexts.append(Context(
                    sentence=sentence,
                    other_entities=other_entities,
                    relations=entity_relations
                ))
    
    def search(self, query: str) -> List[Entity]:
        """Search for entities containing the query string"""
        return [
            entity for text, entity in self.entities.items()
            if query.lower() in text.lower()
        ]
    
    def get_all_entities(self) -> List[Entity]:
        """Get all entities"""
        return list(self.entities.values())
    
    def get_entity(self, text: str) -> Entity:
        """Get entity by exact text match"""
        return self.entities.get(text)