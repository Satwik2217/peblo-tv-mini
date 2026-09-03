import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.storage import get_storage_backend

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
async def get_catalog():
    storage = get_storage_backend()
    try:
        pointer_data = await storage.read("current.json")
        pointer = json.loads(pointer_data)
        catalogue_data = await storage.read(pointer["file"])
        return Response(content=catalogue_data, media_type="application/json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No catalogue published yet")


@router.get("/catalog/search")
async def search_catalog(
    q: str = None,
    category: str = None,
    language: str = None,
    section: str = None,
):
    storage = get_storage_backend()
    try:
        pointer_data = await storage.read("current.json")
        pointer = json.loads(pointer_data)
        catalogue_data = json.loads(await storage.read(pointer["file"]))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No catalogue published yet")

    results = {"sections": {}}

    for section_name, section_data in catalogue_data.get("sections", {}).items():
        if section and section != section_name:
            continue

        matching_shows = []
        for show in section_data.get("shows", []):
            show_match = True

            # Category filter
            if category:
                if category not in show.get("categories", []):
                    show_match = False

            # Search query
            if q:
                q_lower = q.lower()
                title_match = q_lower in show.get("title", "").lower()
                category_match = any(q_lower in c.lower() for c in show.get("categories", []))

                # Check episode titles
                ep_match = False
                for season_data in show.get("seasons", {}).values():
                    for ep in season_data.get("episodes", []):
                        if q_lower in ep.get("title", "").lower():
                            ep_match = True
                            break

                if not (title_match or category_match or ep_match):
                    show_match = False

            if not show_match:
                continue

            # Language filter: check if any episode has this language
            if language:
                has_lang = False
                for season_data in show.get("seasons", {}).values():
                    for ep in season_data.get("episodes", []):
                        if language in ep.get("languages", []):
                            has_lang = True
                            break
                    if has_lang:
                        break
                if not has_lang:
                    continue

            matching_shows.append(show)

        if matching_shows:
            results["sections"][section_name] = {
                "name": section_name,
                "shows": matching_shows,
            }

    results["meta"] = {
        "total_shows": sum(len(s.get("shows", [])) for s in results["sections"].values()),
    }

    return results
