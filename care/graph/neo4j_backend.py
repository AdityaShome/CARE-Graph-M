from __future__ import annotations
import os
from care.jury.models import EvidenceObject


class Neo4jBackend:
    def __init__(self) -> None:
        from neo4j import GraphDatabase
        uri = os.environ.get("CARE_NEO4J_URI", "bolt://127.0.0.1:7687")
        user = os.environ.get("CARE_NEO4J_USER", "neo4j")
        password = os.environ.get("CARE_NEO4J_PASSWORD", "password")
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Evidence) REQUIRE e.source_id IS UNIQUE")

    def add(self, objects: list[EvidenceObject]) -> None:
        with self._driver.session() as session:
            for obj in objects:
                session.run(
                    """MERGE (e:Evidence {source_id: $sid})
                    SET e.source_type=$st, e.content=$c, e.reliability=$r""",
                    sid=obj.source_id,
                    st=obj.source_type,
                    c=obj.content,
                    r=obj.reliability_score,
                )

    def search(self, query: str, top_k: int = 5) -> list[EvidenceObject]:
        with self._driver.session() as session:
            result = session.run(
                "MATCH (e:Evidence) WHERE toLower(e.content) CONTAINS toLower($q) RETURN e LIMIT $k",
                q=query,
                k=top_k,
            )
            return [
                EvidenceObject(
                    source_id=r["e"]["source_id"],
                    source_type=r["e"]["source_type"],
                    content=r["e"]["content"],
                    reliability_score=r["e"].get("reliability", 0.5),
                )
                for r in result
            ]
