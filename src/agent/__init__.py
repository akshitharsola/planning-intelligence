"""Planning Q&A agent prototype (standalone; does not touch src/web or the chat service).

Answers come only from the database: application facts from dhlgh_applications and
reasons/conditions from validated decision_items, quoted verbatim with their source.
An LLM (Ollama), when available, only helps interpret the question.
"""
