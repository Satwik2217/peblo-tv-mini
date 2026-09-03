from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.show import Show
from app.models.season import Season
from app.models.episode import Episode
from app.models.artwork import Artwork
from app.models.user import User
from app.auth import require_editor_or_admin

router = APIRouter(prefix="/admin/validation-report", tags=["validation"])


@router.get("")
async def get_validation_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    issues = {
        "shows": [],
        "episodes": [],
        "artwork": [],
        "duplicates": [],
    }

    # Load all shows
    shows_result = await db.execute(select(Show))
    shows = {s.id: s for s in shows_result.scalars().all()}

    # Load all seasons
    seasons_result = await db.execute(select(Season))
    seasons = {s.id: s for s in seasons_result.scalars().all()}

    # Load all episodes
    episodes_result = await db.execute(select(Episode))
    episodes = episodes_result.scalars().all()

    # Check shows
    for show in shows.values():
        status_val = show.status.value if hasattr(show.status, 'value') else show.status
        if status_val == "published" and not show.section:
            issues["shows"].append({
                "show_id": show.id,
                "show_title": show.title,
                "message": f'Show "{show.title}" is published but has no section.',
            })

    # Check episodes
    for ep in episodes:
        ep_status = ep.status.value if hasattr(ep.status, 'value') else ep.status
        season = seasons.get(ep.season_id)
        if not season:
            issues["episodes"].append({
                "episode_id": ep.id,
                "episode_title": ep.title,
                "message": f'Episode "{ep.title}" references missing season.',
            })
            continue

        show = shows.get(season.show_id)

        if ep_status == "published":
            if not ep.duration_seconds:
                issues["episodes"].append({
                    "episode_id": ep.id,
                    "episode_title": ep.title,
                    "show_title": show.title if show else "Unknown",
                    "message": f'Episode "{ep.title}" is published but has no duration.',
                })

            # Check artwork
            artwork_result = await db.execute(
                select(Artwork).where(Artwork.episode_id == ep.id)
            )
            artworks = artwork_result.scalars().all()
            if not artworks:
                issues["episodes"].append({
                    "episode_id": ep.id,
                    "episode_title": ep.title,
                    "show_title": show.title if show else "Unknown",
                    "message": f'Episode "{ep.title}" is published but has no artwork.',
                })
            else:
                artwork_types = {a.artwork_type for a in artworks}
                for expected_type in ["poster", "banner", "thumbnail"]:
                    if expected_type not in artwork_types:
                        issues["artwork"].append({
                            "episode_id": ep.id,
                            "episode_title": ep.title,
                            "show_title": show.title if show else "Unknown",
                            "message": f'Episode "{ep.title}" is missing {expected_type} artwork.',
                        })

    # Check duplicates: content_group + language
    seen_cg_lang = defaultdict(list)
    for ep in episodes:
        key = (ep.content_group, ep.language)
        seen_cg_lang[key].append(ep)

    for (cg, lang), eps in seen_cg_lang.items():
        if len(eps) > 1:
            ep_titles = [f'"{e.title}" (id={e.id})' for e in eps]
            issues["duplicates"].append({
                "content_group": cg,
                "language": lang,
                "episode_ids": [e.id for e in eps],
                "message": f'Duplicate content_group "{cg}" + language "{lang}" found in episodes: {", ".join(ep_titles)}.',
            })

    # Summary
    total_blocking = (
        len(issues["shows"])
        + len([e for e in issues["episodes"] if "no duration" in e["message"] or "no artwork" in e["message"]])
        + len([a for a in issues["artwork"] if "missing" in a["message"]])
        + len(issues["duplicates"])
    )

    return {
        "issues": issues,
        "total_blocking": total_blocking,
        "summary": {
            "shows_with_issues": len(issues["shows"]),
            "episodes_with_issues": len(issues["episodes"]),
            "artwork_issues": len(issues["artwork"]),
            "duplicate_issues": len(issues["duplicates"]),
        },
    }
