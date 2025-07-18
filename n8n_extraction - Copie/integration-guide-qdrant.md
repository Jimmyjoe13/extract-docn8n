# Guide d'Intégration : README.md et Métadonnées dans Qdrant

## Vue d'ensemble

Ce guide explique comment intégrer efficacement le README.md et les métadonnées dans votre base de données vectorielle Qdrant pour optimiser votre agent de génération de workflows n8n.

## Structure des Collections Qdrant

### 1. Collection Principale : `n8n_documentation`
```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration de la collection principale
client = QdrantClient("localhost", port=6333)

client.create_collection(
    collection_name="n8n_documentation",
    vectors_config=models.VectorParams(
        size=1536,  # Taille pour OpenAI text-embedding-3-small
        distance=models.Distance.COSINE
    )
)
```

### 2. Collection Guide : `n8n_navigation_guide`
```python
# Collection séparée pour le README et métadonnées
client.create_collection(
    collection_name="n8n_navigation_guide",
    vectors_config=models.VectorParams(
        size=1536,
        distance=models.Distance.COSINE
    )
)
```

## Intégration du README.md

### 1. Chunking Intelligent du README
```python
def chunk_readme_for_agent(readme_content):
    """
    Divise le README en chunks logiques pour l'agent
    """
    chunks = []
    
    # Chunk 1: Navigation Strategy
    navigation_chunk = extract_section(readme_content, "STRUCTURE DE NAVIGATION PRIORITAIRE")
    chunks.append({
        "content": navigation_chunk,
        "type": "navigation_guide",
        "priority": "high",
        "use_case": "component_selection"
    })
    
    # Chunk 2: Workflow Patterns
    patterns_chunk = extract_section(readme_content, "PATTERNS DE WORKFLOWS TYPES")
    chunks.append({
        "content": patterns_chunk,
        "type": "workflow_patterns",
        "priority": "high",
        "use_case": "workflow_generation"
    })
    
    # Chunk 3: Rules and Optimization
    rules_chunk = extract_section(readme_content, "RÈGLES DE GÉNÉRATION DE WORKFLOWS")
    chunks.append({
        "content": rules_chunk,
        "type": "generation_rules",
        "priority": "medium",
        "use_case": "validation"
    })
    
    return chunks

# Vectorisation et insertion
readme_chunks = chunk_readme_for_agent(readme_content)
for i, chunk in enumerate(readme_chunks):
    client.upsert(
        collection_name="n8n_navigation_guide",
        points=[
            models.PointStruct(
                id=f"readme_chunk_{i}",
                vector=embed_text(chunk["content"]),
                payload=chunk
            )
        ]
    )
```

### 2. Métadonnées Enrichies pour Documentation
```python
def create_documentation_point(doc_content, doc_metadata):
    """
    Crée un point Qdrant avec métadonnées optimisées
    """
    # Métadonnées de base
    payload = {
        "content": doc_content,
        "url": doc_metadata.get("url", ""),
        "title": doc_metadata.get("title", ""),
        
        # Métadonnées de classification
        "category": doc_metadata.get("category", "unknown"),
        "node_type": doc_metadata.get("node_type", "unknown"),
        "complexity": doc_metadata.get("complexity", "intermediate"),
        "use_case": doc_metadata.get("use_case", []),
        "integration_type": doc_metadata.get("integration_type", "unknown"),
        "workflow_pattern": doc_metadata.get("workflow_pattern", []),
        
        # Métadonnées pour l'agent
        "agent_hints": {
            "is_trigger": doc_metadata.get("category") == "trigger",
            "is_action": doc_metadata.get("category") == "action",
            "is_ai_related": doc_metadata.get("node_type") == "langchain",
            "complexity_score": {"beginner": 1, "intermediate": 2, "advanced": 3}.get(
                doc_metadata.get("complexity", "intermediate"), 2
            )
        },
        
        # Relations avec autres nodes
        "related_nodes": doc_metadata.get("related_nodes", []),
        "compatible_with": doc_metadata.get("compatible_with", []),
        
        # Contexte d'utilisation
        "common_workflows": doc_metadata.get("common_workflows", []),
        "performance_tips": doc_metadata.get("performance_tips", [])
    }
    
    return models.PointStruct(
        id=generate_unique_id(doc_metadata),
        vector=embed_text(doc_content),
        payload=payload
    )

# Exemple d'insertion
doc_point = create_documentation_point(
    doc_content="Documentation du node Webhook Trigger...",
    doc_metadata={
        "url": "https://docs.n8n.io/integrations/builtin/trigger-nodes/webhook-trigger/",
        "title": "Webhook Trigger Node",
        "category": "trigger",
        "node_type": "trigger",
        "complexity": "beginner",
        "use_case": ["api_automation", "webhook_handling"],
        "integration_type": "http",
        "workflow_pattern": ["api_automation"],
        "related_nodes": ["HTTP Request", "Respond to Webhook", "IF"],
        "common_workflows": ["API automation", "Real-time data processing"]
    }
)

client.upsert(
    collection_name="n8n_documentation",
    points=[doc_point]
)
```

## Stratégies de Recherche pour l'Agent

### 1. Recherche Hiérarchique
```python
class N8nWorkflowAgent:
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        
    def generate_workflow(self, user_request):
        """
        Génère un workflow en utilisant la recherche hiérarchique
        """
        # Étape 1: Consulter le guide de navigation
        navigation_context = self.get_navigation_context(user_request)
        
        # Étape 2: Rechercher les composants appropriés
        components = self.search_components(user_request, navigation_context)
        
        # Étape 3: Assembler le workflow
        workflow = self.assemble_workflow(components, navigation_context)
        
        return workflow
    
    def get_navigation_context(self, user_request):
        """
        Récupère le contexte de navigation depuis le README
        """
        search_results = self.client.search(
            collection_name="n8n_navigation_guide",
            query_vector=embed_text(user_request),
            limit=5,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="priority",
                        match=models.MatchValue(value="high")
                    )
                ]
            )
        )
        
        return {
            "patterns": extract_patterns(search_results),
            "rules": extract_rules(search_results),
            "component_priorities": extract_priorities(search_results)
        }
    
    def search_components(self, user_request, navigation_context):
        """
        Recherche les composants avec filtres intelligents
        """
        # Déterminer les filtres basés sur le contexte
        filters = self.determine_filters(user_request, navigation_context)
        
        # Recherche avec filtres
        results = self.client.search(
            collection_name="n8n_documentation",
            query_vector=embed_text(user_request),
            limit=10,
            query_filter=models.Filter(must=filters)
        )
        
        return results
    
    def determine_filters(self, user_request, navigation_context):
        """
        Détermine les filtres appropriés basés sur le contexte
        """
        filters = []
        
        # Analyser le type de requête
        if "schedule" in user_request.lower() or "daily" in user_request.lower():
            filters.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value="trigger")
                )
            )
            filters.append(
                models.FieldCondition(
                    key="use_case",
                    match=models.MatchAny(any=["scheduling"])
                )
            )
        
        if "email" in user_request.lower():
            filters.append(
                models.FieldCondition(
                    key="integration_type",
                    match=models.MatchValue(value="email")
                )
            )
        
        if "ai" in user_request.lower() or "chatbot" in user_request.lower():
            filters.append(
                models.FieldCondition(
                    key="node_type",
                    match=models.MatchValue(value="langchain")
                )
            )
        
        return filters
```

### 2. Recherche Contextuelle Avancée
```python
def advanced_search_strategy(client, user_request, context):
    """
    Stratégie de recherche avancée avec pondération
    """
    # Recherche multi-étapes
    
    # 1. Recherche de patterns
    pattern_results = client.search(
        collection_name="n8n_navigation_guide",
        query_vector=embed_text(user_request),
        limit=3,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="type",
                    match=models.MatchValue(value="workflow_patterns")
                )
            ]
        )
    )
    
    # 2. Recherche de composants par catégorie
    component_searches = {}
    for category in ["trigger", "action", "transform"]:
        results = client.search(
            collection_name="n8n_documentation",
            query_vector=embed_text(user_request),
            limit=5,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="category",
                        match=models.MatchValue(value=category)
                    )
                ]
            )
        )
        component_searches[category] = results
    
    # 3. Combiner les résultats avec pondération
    weighted_results = combine_and_weight_results(
        pattern_results, component_searches, user_request
    )
    
    return weighted_results
```

## Configuration Optimisée

### 1. Configuration Qdrant
```python
# Optimisations pour performance
client.update_collection(
    collection_name="n8n_documentation",
    optimizer_config=models.OptimizersConfig(
        deleted_threshold=0.2,
        vacuum_min_vector_number=1000,
        default_segment_number=0,
        max_segment_size=None,
        memmap_threshold=None,
        indexing_threshold=20000,
        flush_interval_sec=5,
        max_optimization_threads=1
    )
)
```

### 2. Index sur Métadonnées
```python
# Création d'index pour recherche rapide
client.create_payload_index(
    collection_name="n8n_documentation",
    field_name="category",
    field_schema=models.PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="n8n_documentation",
    field_name="node_type",
    field_schema=models.PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="n8n_documentation",
    field_name="complexity",
    field_schema=models.PayloadSchemaType.KEYWORD
)
```

## Exemple d'Utilisation Complète

```python
# Initialisation
agent = N8nWorkflowAgent(client)

# Requête utilisateur
user_request = "Je veux créer un workflow qui traite les emails entrants et génère des réponses automatiques avec OpenAI"

# Génération du workflow
workflow = agent.generate_workflow(user_request)

# Résultat attendu:
# {
#   "workflow_name": "Email Auto-Response with AI",
#   "nodes": [
#     {
#       "type": "Email Trigger",
#       "config": {...},
#       "position": 1
#     },
#     {
#       "type": "IF",
#       "config": {...},
#       "position": 2
#     },
#     {
#       "type": "OpenAI",
#       "config": {...},
#       "position": 3
#     },
#     {
#       "type": "Email Send",
#       "config": {...},
#       "position": 4
#     }
#   ],
#   "connections": [...],
#   "metadata": {...}
# }
```

## Maintenance et Optimisation

### 1. Monitoring des Performances
```python
# Suivi des métriques de recherche
def monitor_search_performance(client, collection_name):
    collection_info = client.get_collection(collection_name)
    return {
        "total_points": collection_info.points_count,
        "vector_size": collection_info.config.params.vectors.size,
        "distance_function": collection_info.config.params.vectors.distance,
        "indexed_fields": collection_info.payload_schema
    }
```

### 2. Mise à jour des Métadonnées
```python
def update_document_metadata(client, document_id, new_metadata):
    """
    Met à jour les métadonnées d'un document
    """
    client.set_payload(
        collection_name="n8n_documentation",
        payload=new_metadata,
        points=[document_id]
    )
```

Ce guide vous permettra d'intégrer efficacement le README.md et les métadonnées dans votre base de données vectorielle Qdrant pour optimiser votre agent de génération de workflows n8n.