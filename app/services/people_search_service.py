from __future__ import annotations

import asyncio
from typing import Any
import httpx

from app.core.config import get_settings


class PeopleSearchService:
    """Apollo/PDL adapter with a deterministic demo fallback when no key is configured."""

    PDL_URL = "https://api.peopledatalabs.com/v5/person/search"
    APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"
    APOLLO_ENRICH_URL = "https://api.apollo.io/api/v1/people/match"

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def active_source(self) -> str:
        if self.settings.APOLLO_API_KEY:
            return "APOLLO"
        if self.settings.PDL_API_KEY:
            return "PDL"
        return "DEMO"

    async def search(self, *, query: str, location: str | None, limit: int) -> list[dict[str, Any]]:
        if self.settings.APOLLO_API_KEY:
            return await self._search_apollo(query, location, limit)
        if self.settings.PDL_API_KEY:
            return await self._search_pdl(query, location, limit)
        return self._demo_results(query, location, limit)

    async def _search_pdl(self, query: str, location: str | None, limit: int) -> list[dict[str, Any]]:
        must = {"exists": "work_email"}
        payload = {
            "size": limit,
            "query": {"bool": {"must": [must, {"term": {"job_title": query}}]}},
        }
        if location:
            payload["query"]["bool"]["must"].append({"match": {"location_name": location}})

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.PDL_URL, headers={"X-Api-Key": self.settings.PDL_API_KEY}, json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"People Data Labs API {response.status_code}: {response.text[:500]}")
        data = response.json()
        return data.get("data", [])

    async def _search_apollo(self, query: str, location: str | None, limit: int) -> list[dict[str, Any]]:
        headers = {"x-api-key": self.settings.APOLLO_API_KEY, "accept": "application/json"}
        params: dict[str, Any] = {"per_page": limit}
        if query:
            params["person_titles[]"] = query
        if location:
            params["person_locations[]"] = location

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.APOLLO_SEARCH_URL, headers=headers, params=params)
            if response.status_code >= 400:
                raise RuntimeError(f"Apollo API {response.status_code}: {response.text[:500]}")
            matches = response.json().get("people", [])[:limit]

            # The search endpoint masks names and omits contact info entirely;
            # each match needs a separate enrichment call to reveal it.
            enrich_responses = await asyncio.gather(
                *[
                    client.post(
                        self.APOLLO_ENRICH_URL,
                        headers=headers,
                        params={"id": match["id"], "reveal_personal_emails": "true"},
                    )
                    for match in matches
                ]
            )

        results = []
        for resp in enrich_responses:
            if resp.status_code >= 400:
                continue
            person = resp.json().get("person") or {}
            phones = person.get("phone_numbers") or []
            location_name = ", ".join(
                part for part in (person.get("city"), person.get("state"), person.get("country")) if part
            )
            results.append(
                {
                    "full_name": person.get("name"),
                    "work_email": person.get("email"),
                    "mobile_phone": phones[0].get("sanitized_number") if phones else None,
                    "job_title": person.get("title"),
                    "location_name": location_name or None,
                    "linkedin_url": person.get("linkedin_url"),
                }
            )
        return results

    @staticmethod
    def _demo_results(query: str, location: str | None, limit: int) -> list[dict[str, Any]]:
        people = [
            {
                "full_name": "Pavan Sekhar Mandavilli",
                "work_email": "pavanmandavilli24@gmail.com",
                "mobile_phone": "+918074984348",
                "linkedin_url": None,
            },
            *(
                {
                    "full_name": name,
                    "work_email": f"{name.lower().replace(' ', '.')}@example.com",
                    "mobile_phone": None,
                    "linkedin_url": f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
                }
                for name in ["Aarav Sharma", "Priya Nair", "Rahul Verma", "Sneha Reddy", "Vikram Singh", "Ananya Rao"]
            ),
        ]
        return [
            {
                **person,
                "job_title": query or "Software Engineer",
                "location_name": location or "Bengaluru, India",
            }
            for person in people[:limit]
        ]
