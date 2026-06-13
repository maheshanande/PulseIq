import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.models.entity import Entity
from pulseiq_backend.repositories.entity_repo import EntityRepository
from pulseiq_backend.services.llm import ollama_client

logger = logging.getLogger(__name__)

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_IDENTIFIER_PATTERN = re.compile(r"\b(?:[a-z]+[-_#]?\d+[a-z0-9-]*|\d+[a-z0-9-]*)\b", re.IGNORECASE)

_RESOLUTION_PROMPT = """\
You are an entity resolution system for a business operations platform.

New entity detected:
- Type: {entity_type}
- Name: "{name}"

Existing entities of the same type:
{existing}

Task: Does the new entity refer to the same real-world entity as any existing one?
Consider abbreviations, alternate names, and common business aliases.

Reply with ONLY one of:
- "MATCH: <existing_name>" if it matches an existing entity
- "NEW" if it is a genuinely new entity

No explanation.
"""


class EntityResolver:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = EntityRepository(db)

    async def resolve(
        self,
        tenant_id: uuid.UUID,
        entity_type: str,
        name: str,
        aliases: list[str],
    ) -> Entity:
        canonical_name = canonicalize_entity_name(name)
        canonical_aliases = [canonicalize_entity_name(alias) for alias in aliases if alias.strip()]

        # Stage 1: exact match on name or known aliases
        entity = await self._repo.find_by_name_or_alias(tenant_id, canonical_name)
        if entity:
            await self._merge_aliases(entity, canonical_aliases + [canonical_name])
            return entity

        # Stage 2: AI-assisted fuzzy match against existing entities of same type
        existing = await self._repo.find_by_type(tenant_id, entity_type)
        if existing:
            compatible_existing = filter_identifier_compatible_entities(canonical_name, existing)
            if not compatible_existing:
                logger.info("Treating %s as a new entity because explicit identifiers do not match existing %s entities", canonical_name, entity_type)
            matched = await self._llm_resolve(entity_type, canonical_name, compatible_existing) if compatible_existing else None
            if matched:
                await self._merge_aliases(matched, canonical_aliases + [canonical_name])
                return matched

        # Stage 3: genuinely new entity
        all_aliases = list({a for a in canonical_aliases if a.lower() != canonical_name.lower()})
        entity = await self._repo.create(tenant_id, entity_type, canonical_name, all_aliases)
        logger.info("Created new entity: %s (%s)", canonical_name, entity_type)
        return entity

    async def _llm_resolve(self, entity_type: str, name: str, existing: list[Entity]) -> Entity | None:
        existing_list = "\n".join(
            f"- {e.name} (aliases: {', '.join(e.aliases) or 'none'})" for e in existing
        )
        prompt = _RESOLUTION_PROMPT.format(
            entity_type=entity_type, name=name, existing=existing_list
        )
        raw = (await ollama_client.generate(prompt)).strip()
        if raw.startswith("MATCH:"):
            matched_name = raw.removeprefix("MATCH:").strip()
            return next((e for e in existing if e.name.lower() == matched_name.lower()), None)
        return None

    async def _merge_aliases(self, entity: Entity, new_aliases: list[str]) -> None:
        for alias in new_aliases:
            if alias.lower() != entity.name.lower():
                await self._repo.add_alias(entity, alias)


def canonicalize_entity_name(name: str) -> str:
    """Normalize entity names while preserving explicit identifiers like Machine 2."""
    tokens = _TOKEN_PATTERN.findall(name.lower())
    if not tokens:
        return name.strip()
    return " ".join(tokens).title()


def entity_identifiers(name: str) -> set[str]:
    normalized = name.lower().replace("_", "-")
    return {match.group(0).strip("-#") for match in _IDENTIFIER_PATTERN.finditer(normalized)}


def filter_identifier_compatible_entities(name: str, existing: list[Entity]) -> list[Entity]:
    identifiers = entity_identifiers(name)
    if not identifiers:
        return existing

    compatible = []
    for entity in existing:
        candidate_names = [entity.name, *entity.aliases]
        candidate_identifiers = set().union(*(entity_identifiers(candidate) for candidate in candidate_names))
        if identifiers & candidate_identifiers:
            compatible.append(entity)
    return compatible
