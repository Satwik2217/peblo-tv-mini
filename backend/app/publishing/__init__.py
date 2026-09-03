import json
from datetime import datetime
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.show import Show
from app.models.season import Season
from app.models.episode import Episode
from app.models.artwork import Artwork
from app.models.publish_run import PublishRun, PublishStatus
from app.models.user import User
from app.storage import get_storage_backend


async def run_publish(user: User, db: AsyncSession) -> PublishRun:
    storage = get_storage_backend()

    publish_run = PublishRun(
        initiated_by=user.id,
        started_at=datetime.utcnow(),
        status=PublishStatus.failed,
    )
    db.add(publish_run)
    await db.flush()
    await db.refresh(publish_run)

    errors = []

    try:
        # Load all data
        shows_result = await db.execute(select(Show))
        shows = {s.id: s for s in shows_result.scalars().all()}

        seasons_result = await db.execute(select(Season))
        seasons = {s.id: s for s in seasons_result.scalars().all()}

        episodes_result = await db.execute(select(Episode))
        episodes = episodes_result.scalars().all()

        # Load all artwork
        artworks_result = await db.execute(select(Artwork))
        all_artworks = artworks_result.scalars().all()
        episode_artworks = {}
        show_artworks = {}
        for a in all_artworks:
            if a.episode_id:
                episode_artworks.setdefault(a.episode_id, []).append(a)
            if a.show_id:
                show_artworks.setdefault(a.show_id, []).append(a)

        # Filter published shows
        published_shows = []
        for show in shows.values():
            status_val = show.status.value if hasattr(show.status, 'value') else show.status
            if status_val != "published":
                continue
            if not show.section:
                errors.append(f'Show "{show.title}" (id={show.id}) has no section - skipped.')
                continue
            published_shows.append(show)

        # Group episodes by content_group
        content_groups: Dict[str, List[Episode]] = {}
        published_episode_count = 0
        skipped_episodes = 0

        for ep in episodes:
            ep_status = ep.status.value if hasattr(ep.status, 'value') else ep.status
            if ep_status != "published":
                continue

            season = seasons.get(ep.season_id)
            if not season:
                errors.append(f'Episode "{ep.title}" (id={ep.id}) has no valid season - skipped.')
                skipped_episodes += 1
                continue

            show = shows.get(season.show_id)
            if not show or show not in published_shows:
                skipped_episodes += 1
                continue

            # Validate: must have artwork and duration
            if not ep.duration_seconds:
                errors.append(f'Episode "{ep.title}" (id={ep.id}) has no duration - skipped.')
                skipped_episodes += 1
                continue

            ep_artworks = episode_artworks.get(ep.id, [])
            if not ep_artworks:
                errors.append(f'Episode "{ep.title}" (id={ep.id}) has no artwork - skipped.')
                skipped_episodes += 1
                continue

            content_groups.setdefault(ep.content_group, []).append(ep)
            published_episode_count += 1

        # Build catalogue
        catalogue = {
            "version": publish_run.id,
            "generated_at": datetime.utcnow().isoformat(),
            "sections": {},
        }

        # Group by section
        section_shows: Dict[str, List] = {}
        for show in published_shows:
            section_shows.setdefault(show.section, []).append(show)

        for section_name in sorted(section_shows.keys()):
            section_data = {
                "name": section_name,
                "shows": [],
            }

            # Sort shows alphabetically by title
            for show in sorted(section_shows[section_name], key=lambda s: s.title):
                show_section = {
                    "id": show.id,
                    "title": show.title,
                    "slug": show.slug,
                    "synopsis": show.synopsis or "",
                    "categories": json.loads(show.categories) if show.categories else [],
                    "artwork": {},
                    "seasons": {},
                }

                # Add show artwork
                for art in show_artworks.get(show.id, []):
                    show_section["artwork"][art.artwork_type] = storage.public_url(art.storage_key)

                # Group episodes by season
                show_seasons = [s for s in seasons.values() if s.show_id == show.id]
                show_seasons.sort(key=lambda s: s.season_number)

                for season in show_seasons:
                    if season.season_number == 0:
                        # Season 0: trailers
                        season_cg = {}
                        for ep in episodes:
                            if ep.season_id == season.id:
                                ep_status = ep.status.value if hasattr(ep.status, 'value') else ep.status
                                if ep_status == "published" and ep.duration_seconds:
                                    season_cg.setdefault(ep.content_group, []).append(ep)

                        if season_cg:
                            trailers = []
                            for cg, cg_eps in sorted(season_cg.items()):
                                langs = sorted(set(e.language for e in cg_eps))
                                ep_with_art = next((e for e in cg_eps if episode_artworks.get(e.id)), cg_eps[0])
                                ep_art = episode_artworks.get(ep_with_art.id, [])
                                trailer_entry = {
                                    "content_group": cg,
                                    "title": ep_with_art.title,
                                    "languages": langs,
                                    "duration_seconds": ep_with_art.duration_seconds,
                                    "artwork": {a.artwork_type: storage.public_url(a.storage_key) for a in ep_art},
                                }
                                trailers.append(trailer_entry)
                            if trailers:
                                show_section["trailers"] = trailers
                    else:
                        # Normal season
                        season_key = f"season_{season.season_number}"
                        season_data_entry = {
                            "season_number": season.season_number,
                            "title": season.title or f"Season {season.season_number}",
                            "episodes": [],
                        }

                        # Group by content_group within this season
                        season_cg: Dict[str, List[Episode]] = {}
                        for ep in episodes:
                            if ep.season_id == season.id:
                                ep_status = ep.status.value if hasattr(ep.status, 'value') else ep.status
                                if ep_status == "published":
                                    season_cg.setdefault(ep.content_group, []).append(ep)

                        for cg, cg_eps in sorted(season_cg.items()):
                            # Validate content_group uniqueness
                            lang_set = set(e.language for e in cg_eps)
                            if len(lang_set) != len(cg_eps):
                                # Duplicate language in same content_group - take first
                                seen = set()
                                unique_eps = []
                                for e in cg_eps:
                                    if e.language not in seen:
                                        seen.add(e.language)
                                        unique_eps.append(e)
                                cg_eps = unique_eps
                                errors.append(f'Duplicate language in content_group "{cg}" - using first occurrence.')

                            langs = sorted(lang_set)
                            ep_with_art = next((e for e in cg_eps if episode_artworks.get(e.id)), cg_eps[0])
                            ep_art = episode_artworks.get(ep_with_art.id, [])

                            # Get episode-level artwork, fallback to show artwork
                            ep_art_dict = {}
                            for a in ep_art:
                                ep_art_dict[a.artwork_type] = storage.public_url(a.storage_key)

                            # Fill missing artwork types from show
                            for at in ["poster", "banner", "thumbnail"]:
                                if at not in ep_art_dict and at in show_section["artwork"]:
                                    ep_art_dict[at] = show_section["artwork"][at]

                            ep_entry = {
                                "content_group": cg,
                                "title": ep_with_art.title,
                                "episode_number": ep_with_art.episode_number,
                                "synopsis": ep_with_art.synopsis or "",
                                "duration_seconds": ep_with_art.duration_seconds,
                                "languages": langs,
                                "artwork": ep_art_dict,
                            }
                            season_data_entry["episodes"].append(ep_entry)

                        # Sort episodes by episode_number
                        season_data_entry["episodes"].sort(key=lambda e: e["episode_number"])
                        show_section["seasons"][season_key] = season_data_entry

                section_data["shows"].append(show_section)

            # Sort shows alphabetically
            section_data["shows"].sort(key=lambda s: s["title"])
            catalogue["sections"][section_name] = section_data

        # Add global metadata
        catalogue["meta"] = {
            "total_shows": sum(len(s.get("shows", [])) for s in catalogue["sections"].values()),
            "total_episodes": published_episode_count,
        }

        # Write catalogue atomically
        version_num = publish_run.id
        catalogue_filename = f"catalogue-v{version_num}.json"
        await storage.save(catalogue_filename, json.dumps(catalogue, indent=2).encode(), "application/json")

        # Atomic pointer swap
        pointer_data = json.dumps({"version": version_num, "file": catalogue_filename})
        await storage.save("current.json", pointer_data.encode(), "application/json")

        # Update publish run
        publish_run.completed_at = datetime.utcnow()
        publish_run.status = PublishStatus.success
        publish_run.shows_count = catalogue["meta"]["total_shows"]
        publish_run.episodes_count = published_episode_count
        publish_run.catalogue_version = catalogue_filename
        if errors:
            publish_run.errors = json.dumps(errors)
        await db.flush()
        await db.refresh(publish_run)

    except Exception as e:
        publish_run.completed_at = datetime.utcnow()
        publish_run.status = PublishStatus.failed
        publish_run.errors = json.dumps([str(e)])
        await db.flush()
        await db.refresh(publish_run)

    return publish_run
