Script d'extraction n8n avec priorisation LangChain Agent IA
Modifications apportées au script original
J'ai complètement mis à jour le script pour intégrer automatiquement toutes les URLs liées aux nodes LangChain Agent IA comme priorité #1 dans le système d'extraction. Le script détecte désormais intelligemment ces URLs grâce à des expressions régulières spécialisées.

Nouveau système de priorités
Le script utilise maintenant un système de catégorisation hiérarchique où les nodes LangChain Agent IA sont traités en premier :

Priorité	Catégorie	URLs concernées
1	langchain_agent	Tous les nodes LangChain, AI Agent, LangChain Code
2	workflows	Gestion des workflows
3	other	Pages générales, glossaire, guides
4	code	Code, expressions, transformations
5	hosting	Hébergement, configuration
6	user_management	Gestion utilisateurs, RBAC
7	integrations	Intégrations tierces
Détection automatique des URLs LangChain
Le script recherche automatiquement ces patterns dans la sitemap n8n :

python
'langchain_agent': {
    'patterns': [
        r'/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain\.agent',
        r'/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain\.code',
        r'/integrations/builtin/cluster-nodes/.*langchain',
        r'/advanced-ai/langchain',
        r'/advanced-ai/.*agent',
        r'/code/builtin/langchain-methods',
        r'/integrations/builtin/cluster-nodes/sub-nodes/.*langchain',
        r'/integrations/builtin/core-nodes/n8n-nodes-langchain',
    ],
    'priority': 1
}
