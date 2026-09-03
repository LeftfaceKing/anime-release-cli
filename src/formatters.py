from datetime import datetime


def format_date(date_data):

    if not date_data:

        return "TBA"

    year = date_data.get(
        "year"
    )

    month = date_data.get(
        "month"
    )

    day = date_data.get(
        "day"
    )

    if not all(
        [
            year,
            month,
            day,
        ]
    ):

        return "TBA"

    return (
        f"{month:02d}/"
        f"{day:02d}/"
        f"{year}"
    )


def format_airing_time(timestamp):

    if not timestamp:

        return "TBA"

    dt = datetime.fromtimestamp(
        timestamp
    ).astimezone()

    return dt.strftime(
        "%B %d, %Y at %I:%M %p %Z"
    )


def format_countdown(seconds):

    if seconds is None:

        return "TBA"

    if seconds <= 0:

        return "Airing now / recently aired"

    days, remainder = divmod(
        seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes = (
        remainder
        // 60
    )

    return (
        f"{days}d "
        f"{hours}h "
        f"{minutes}m"
    )


def format_anime_details(anime):

    title = (
        anime[
            "title"
        ][
            "english"
        ]
        or anime[
            "title"
        ][
            "romaji"
        ]
    )

    next_episode = anime.get(
        "nextAiringEpisode"
    )

    studio_nodes = (
        anime.get(
            "studios",
            {},
        ).get(
            "nodes",
            [],
        )
    )

    studios = (
        ", ".join(
            studio["name"]
            for studio in studio_nodes
        )
        or "TBA"
    )

    genres = (
        ", ".join(
            anime.get(
                "genres",
                [],
            )
        )
        or "TBA"
    )

    lines = [
        title.upper(),
        "─" * 50,
        (
            f"Status:          "
            f"{anime.get('status') or 'TBA'}"
        ),
        (
            f"Format:          "
            f"{anime.get('format') or 'TBA'}"
        ),
        (
            f"Episodes:        "
            f"{anime.get('episodes') or 'TBA'}"
        ),
        (
            f"Source:          "
            f"{anime.get('source') or 'TBA'}"
        ),
        (
            f"Studio:          "
            f"{studios}"
        ),
        (
            f"Genres:          "
            f"{genres}"
        ),
        (
            f"Series Start:    "
            f"{format_date(anime.get('startDate'))}"
        ),
        (
            f"Series End:      "
            f"{format_date(anime.get('endDate'))}"
        ),
    ]

    if next_episode:

        episode = next_episode.get(
            "episode"
        )

        episode_text = (
            f"Episode {episode}"
            if episode
            else "Episode TBA"
        )

        lines.extend(
            [
                "",
                (
                    f"Next Episode:    "
                    f"{episode_text}"
                ),
                (
                    f"Air Date:        "
                    f"{format_airing_time(next_episode.get('airingAt'))}"
                ),
                (
                    f"Countdown:       "
                    f"{format_countdown(next_episode.get('timeUntilAiring'))}"
                ),
            ]
        )

    else:

        lines.extend(
            [
                "",
                "Next Episode:    TBA",
                "Air Date:        TBA",
                "Countdown:       TBA",
            ]
        )

    return "\n".join(
        lines
    )