import argparse

from datetime import datetime

from importlib.metadata import (
    version,
    PackageNotFoundError,
)

from api import (
    AniListAPIError,
    KitsuAPIError,
    TsuzukiAPIError,
    get_anime_airing_yesterday,
    get_anime_airing_today,
    get_anime_airing_tomorrow,
    get_anime_entries,
    get_anime_relations,
    get_anime_season,
    get_studio_anime,
    get_tsuzuki_airing_matches,
    get_tsuzuki_anime_schedule,
    get_upcoming_anime,
)

from formatters import (
    format_anime_details,
    format_date,
)


def get_cli_version():

    try:

        return version(
            "anime-release-cli"
        )

    except PackageNotFoundError:

        return "0.1.0"


def anime_title(anime):

    return (
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


def provider_name(anime):

    provider = anime.get(
        "_provider"
    )

    if provider == "kitsu":

        return "Kitsu"

    if provider == "tsuzuki":

        return "Tsuzuki"

    return "AniList"


def print_fallback_notice(
    provider,
):

    if provider == "kitsu":

        print()

        print(
            "AniList is unavailable. "
            "Using Kitsu fallback."
        )

    elif provider == "tsuzuki":

        print()

        print(
            "AniList is unavailable. "
            "Using Tsuzuki schedule fallback."
        )


def print_anime_entry(anime):

    print()

    print(
        anime_title(
            anime
        )
    )

    print(
        f"  Status:   "
        f"{anime.get('status') or 'TBA'}"
    )

    print(
        f"  Format:   "
        f"{anime.get('format') or 'TBA'}"
    )

    print(
        f"  Episodes: "
        f"{anime.get('episodes') or 'TBA'}"
    )

    if (
        anime.get(
            "season"
        )
        and anime.get(
            "seasonYear"
        )
    ):

        print(
            f"  Season:   "
            f"{anime['season'].title()} "
            f"{anime['seasonYear']}"
        )

    studios = (
        anime.get(
            "studios",
            {},
        ).get(
            "nodes",
            [],
        )
    )

    if studios:

        print(
            f"  Studio:   "
            f"{studios[0]['name']}"
        )


def choose_anime(title):

    entries = get_anime_entries(
        title
    )

    if not entries:

        print(
            "No anime found."
        )

        return None

    provider = entries[
        0
    ].get(
        "_provider"
    )

    print_fallback_notice(
        provider
    )

    if len(entries) == 1:

        return entries[0]

    print()

    print(
        f'ENTRIES FOR '
        f'"{title.upper()}"'
    )

    print(
        "─" * 60
    )

    for index, anime in enumerate(
        entries,
        start=1,
    ):

        print()

        print(
            f"{index}. "
            f"{anime_title(anime)}"
        )

        print(
            f"   Status:   "
            f"{anime.get('status') or 'TBA'}"
        )

        print(
            f"   Format:   "
            f"{anime.get('format') or 'TBA'}"
        )

        print(
            f"   Episodes: "
            f"{anime.get('episodes') or 'TBA'}"
        )

        if (
            anime.get(
                "season"
            )
            and anime.get(
                "seasonYear"
            )
        ):

            print(
                f"   Season:   "
                f"{anime['season'].title()} "
                f"{anime['seasonYear']}"
            )

        studios = (
            anime.get(
                "studios",
                {},
            ).get(
                "nodes",
                [],
            )
        )

        if studios:

            print(
                f"   Studio:   "
                f"{studios[0]['name']}"
            )

    while True:

        choice = input(
            "Choose an entry: "
        )

        try:

            choice = int(
                choice
            )

            if (
                1
                <= choice
                <= len(entries)
            ):

                return entries[
                    choice - 1
                ]

        except ValueError:

            pass

        print(
            "Invalid selection."
        )


def handle_search(title):

    anime = choose_anime(
        title
    )

    if anime:

        print()

        print(
            format_anime_details(
                anime
            )
        )

        print()

        print(
            f"Data source: "
            f"{provider_name(anime)}"
        )


def handle_info(title):

    anime = choose_anime(
        title
    )

    if not anime:

        return

    print()

    print(
        format_anime_details(
            anime
        )
    )

    if anime.get(
        "description"
    ):

        print()

        print(
            "Description:"
        )

        print(
            anime[
                "description"
            ]
        )

    print()

    print(
        f"Data source: "
        f"{provider_name(anime)}"
    )


def handle_schedule(title):

    anime = choose_anime(
        title
    )

    if not anime:

        return

    print()

    print(
        format_anime_details(
            anime
        )
    )

    print()

    print(
        "EPISODE SCHEDULE"
    )

    print(
        "─" * 60
    )

    next_episode = anime.get(
        "nextAiringEpisode"
    )

    if not next_episode:

        if anime.get(
            "status"
        ) == "FINISHED":

            print(
                "Series completed."
            )

            print(
                f"Total Episodes: "
                f"{anime.get('episodes') or 'TBA'}"
            )

        else:

            print(
                "No upcoming episode "
                "schedule available."
            )

        return

    episode = next_episode.get(
        "episode"
    )

    date = datetime.fromtimestamp(
        next_episode[
            "airingAt"
        ]
    ).astimezone()

    if episode:

        print(
            f"Episode {episode}"
        )

    else:

        print(
            "Episode TBA"
        )

    print(
        date.strftime(
            "%B %d, %Y at "
            "%I:%M %p %Z"
        )
    )


def handle_relations(title):

    anime = choose_anime(
        title
    )

    if not anime:

        return

    if (
        anime.get(
            "_provider"
        )
        == "kitsu"
    ):

        print()

        print(
            f"RELATIONS — "
            f"{anime_title(anime).upper()}"
        )

        print(
            "─" * 60
        )

        print(
            "Relations are not yet "
            "implemented for the "
            "Kitsu fallback."
        )

        return

    relations = get_anime_relations(
        anime[
            "id"
        ],
        anime.get(
            "_provider",
            "anilist",
        ),
    )

    print()

    print(
        f"RELATIONS — "
        f"{anime_title(anime).upper()}"
    )

    print(
        "─" * 60
    )

    if not relations:

        print(
            "No relations found."
        )

        return

    relation_order = [
        "PREQUEL",
        "SEQUEL",
        "PARENT",
        "SIDE_STORY",
        "SPIN_OFF",
        "ALTERNATIVE",
        "CHARACTER",
        "SUMMARY",
        "COMPILATION",
        "CONTAINS",
        "SOURCE",
        "ADAPTATION",
        "OTHER",
    ]

    grouped = {}

    for relation in relations:

        relation_type = (
            relation.get(
                "relationType"
            )
            or "OTHER"
        )

        node = relation.get(
            "node"
        )

        if not node:

            continue

        grouped.setdefault(
            relation_type,
            [],
        ).append(
            node
        )

    displayed = set()

    for relation_type in (
        relation_order
    ):

        nodes = grouped.get(
            relation_type,
            [],
        )

        if not nodes:

            continue

        displayed.add(
            relation_type
        )

        print()

        print(
            relation_type.replace(
                "_",
                " ",
            )
        )

        for node in nodes:

            title_text = (
                anime_title(
                    node
                )
            )

            media_type = (
                node.get(
                    "type"
                )
                or "TBA"
            )

            anime_format = (
                node.get(
                    "format"
                )
                or "TBA"
            )

            details = [
                media_type,
                anime_format,
            ]

            if (
                node.get(
                    "season"
                )
                and node.get(
                    "seasonYear"
                )
            ):

                details.append(
                    f"{node['season'].title()} "
                    f"{node['seasonYear']}"
                )

            if node.get(
                "episodes"
            ):

                details.append(
                    f"{node['episodes']} "
                    f"episodes"
                )

            print(
                f"  {title_text}"
            )

            print(
                f"    "
                f"{' | '.join(details)}"
            )

    for (
        relation_type,
        nodes,
    ) in grouped.items():

        if relation_type in displayed:

            continue

        print()

        print(
            relation_type.replace(
                "_",
                " ",
            )
        )

        for node in nodes:

            print(
                f"  {anime_title(node)}"
            )


def handle_studio(studio):

    anime_list = get_studio_anime(
        studio
    )

    if not anime_list:

        print(
            "No anime found for studio."
        )

        return

    print(
        studio.upper()
    )

    print(
        "─" * 60
    )

    for anime in anime_list:

        print_anime_entry(
            anime
        )


def handle_season(
    season,
    studio=None,
):

    try:

        season_name, year = (
            season.split(
                "-",
                1,
            )
        )

        year = int(
            year
        )

    except ValueError:

        print(
            "Invalid season. "
            "Use a format such as "
            "fall-2026."
        )

        return

    valid_seasons = {
        "winter",
        "spring",
        "summer",
        "fall",
    }

    if (
        season_name.lower()
        not in valid_seasons
    ):

        print(
            "Invalid season. "
            "Choose winter, spring, "
            "summer, or fall."
        )

        return

    anime_list = get_anime_season(
        season_name,
        year,
    )

    if not anime_list:

        print(
            "No anime found "
            "for that season."
        )

        return

    provider = anime_list[
        0
    ].get(
        "_provider"
    )

    print_fallback_notice(
        provider
    )

    if studio:

        anime_list = [
            anime

            for anime in anime_list

            if any(
                studio.lower()
                in s[
                    "name"
                ].lower()

                for s in anime.get(
                    "studios",
                    {},
                ).get(
                    "nodes",
                    [],
                )
            )
        ]

    print()

    print(
        f"{season_name.upper()} "
        f"{year}"
    )

    print(
        "─" * 60
    )

    if not anime_list:

        print(
            "No matching anime found."
        )

        return

    for anime in anime_list:

        print_anime_entry(
            anime
        )

    print()

    print(
        f"Data source: "
        f"{provider_name(anime_list[0])}"
    )


def handle_upcoming():

    anime_list = get_upcoming_anime()

    if not anime_list:

        print(
            "No upcoming anime found."
        )

        return

    provider = anime_list[
        0
    ].get(
        "_provider"
    )

    print_fallback_notice(
        provider
    )

    print()

    print(
        "UPCOMING ANIME"
    )

    print(
        "─" * 60
    )

    for anime in anime_list:

        title = anime_title(
            anime
        )

        start = format_date(
            anime.get(
                "startDate"
            )
        )

        print()

        print(
            title
        )

        print(
            f"  Start:    {start}"
        )

        if anime.get(
            "format"
        ):

            print(
                f"  Format:   "
                f"{anime['format']}"
            )

    print()

    print(
        f"Data source: "
        f"{provider_name(anime_list[0])}"
    )


def print_airing_schedule(
    schedules,
    heading,
):

    if not schedules:

        print(
            f"No anime airing "
            f"{heading.lower()}."
        )

        return

    provider = schedules[
        0
    ].get(
        "_provider"
    )

    print_fallback_notice(
        provider
    )

    print()

    print(
        f"AIRING {heading.upper()}"
    )

    print(
        "─" * 70
    )

    schedules = sorted(
        schedules,
        key=lambda item: (
            item.get(
                "airingAt"
            )
            or 0
        ),
    )

    for item in schedules:

        title = anime_title(
            item[
                "media"
            ]
        )

        time = datetime.fromtimestamp(
            item[
                "airingAt"
            ]
        ).astimezone()

        episode = item.get(
            "episode"
        )

        episode_text = (
            f"Episode {episode}"
            if episode
            else "Episode TBA"
        )

        if provider == "tsuzuki":

            air_type = (
                item.get(
                    "airType"
                )
                or ""
            ).upper()

            platform = item.get(
                "platform"
            )

            details = []

            if air_type:

                details.append(
                    air_type
                )

            if platform:

                details.append(
                    platform
                )

            detail_text = ""

            if details:

                detail_text = (
                    " | "
                    + " | ".join(
                        details
                    )
                )

            print(
                f"{time.strftime('%I:%M %p')} "
                f"{episode_text} "
                f"{title}"
                f"{detail_text}"
            )

        else:

            print(
                f"{time.strftime('%I:%M %p')} "
                f"{episode_text} "
                f"{title}"
            )

    print()

    if provider == "tsuzuki":

        print(
            "Data source: Tsuzuki"
        )

    else:

        print(
            "Data source: AniList"
        )


def handle_yesterday():

    schedules = (
        get_anime_airing_yesterday()
    )

    print_airing_schedule(
        schedules,
        "YESTERDAY",
    )


def handle_today():

    schedules = get_anime_airing_today()

    print_airing_schedule(
        schedules,
        "TODAY",
    )


def handle_tomorrow():

    schedules = (
        get_anime_airing_tomorrow()
    )

    print_airing_schedule(
        schedules,
        "TOMORROW",
    )


def tsuzuki_title(anime):

    titles = anime.get(
        "title",
        {},
    )

    return (
        titles.get(
            "english"
        )
        or titles.get(
            "romaji"
        )
        or titles.get(
            "native"
        )
        or "Unknown Anime"
    )


def print_tsuzuki_date(
    date_data,
):

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

    if not year:

        return "TBA"

    if not month:

        return str(
            year
        )

    if not day:

        return (
            f"{month:02d}/{year}"
        )

    return (
        f"{month:02d}/"
        f"{day:02d}/"
        f"{year}"
    )


def choose_tsuzuki_airing(
    title,
):

    entries = (
        get_tsuzuki_airing_matches(
            title
        )
    )

    if not entries:

        print()

        print(
            "No airing anime found."
        )

        return None

    if len(entries) == 1:

        return entries[0]

    print()

    print(
        f'AIRING RESULTS FOR '
        f'"{title.upper()}"'
    )

    print(
        "─" * 70
    )

    for index, anime in enumerate(
        entries,
        start=1,
    ):

        print()

        print(
            f"{index}. "
            f"{tsuzuki_title(anime)}"
        )

        print(
            f"   Status:   "
            f"{anime.get('status') or 'TBA'}"
        )

        print(
            f"   Format:   "
            f"{anime.get('format') or 'TBA'}"
        )

        print(
            f"   Episodes: "
            f"{anime.get('episodes') or 'TBA'}"
        )

        studios = (
            anime.get(
                "studios",
                [],
            )
        )

        if studios:

            print(
                f"   Studio:   "
                f"{', '.join(studios)}"
            )

        start_date = (
            anime.get(
                "startDate"
            )
        )

        if start_date:

            print(
                f"   Started:  "
                f"{print_tsuzuki_date(start_date)}"
            )

    while True:

        choice = input(
            "Choose an entry: "
        )

        try:

            choice = int(
                choice
            )

            if (
                1
                <= choice
                <= len(entries)
            ):

                return entries[
                    choice - 1
                ]

        except ValueError:

            pass

        print(
            "Invalid selection."
        )


def print_tsuzuki_note(
    note,
):

    if not note:

        return None

    if isinstance(
        note,
        str,
    ):

        return note

    if isinstance(
        note,
        dict,
    ):

        kind = note.get(
            "kind"
        )

        reason = note.get(
            "reason"
        )

        values = []

        if kind:

            values.append(
                str(kind).upper()
            )

        if reason:

            values.append(
                str(reason)
            )

        if values:

            return " - ".join(
                values
            )

    return None


def handle_airing(title):

    anime = choose_tsuzuki_airing(
        title
    )

    if not anime:

        return

    title_text = tsuzuki_title(
        anime
    )

    print()

    print(
        title_text.upper()
    )

    print(
        "─" * 70
    )

    print(
        f"Status:     "
        f"{anime.get('status') or 'TBA'}"
    )

    print(
        f"Format:     "
        f"{anime.get('format') or 'TBA'}"
    )

    print(
        f"Episodes:   "
        f"{anime.get('episodes') or 'TBA'}"
    )

    print(
        f"Source:     "
        f"{anime.get('source') or 'TBA'}"
    )

    studios = (
        anime.get(
            "studios",
            [],
        )
    )

    if studios:

        print(
            f"Studio:     "
            f"{', '.join(studios)}"
        )

    genres = (
        anime.get(
            "genres",
            [],
        )
    )

    if genres:

        print(
            f"Genres:     "
            f"{', '.join(genres)}"
        )

    start_date = (
        anime.get(
            "startDate"
        )
    )

    if start_date:

        print(
            f"Started:    "
            f"{print_tsuzuki_date(start_date)}"
        )

    streaming = (
        anime.get(
            "streamingOn",
            [],
        )
    )

    if streaming:

        print()

        print(
            "STREAMING"
        )

        print(
            "─" * 70
        )

        for service in streaming:

            site = service.get(
                "site"
            )

            if site:

                print(
                    f"  {site}"
                )

    schedule = (
        get_tsuzuki_anime_schedule(
            anime[
                "id"
            ]
        )
    )

    print()

    print(
        "EPISODE SCHEDULE"
    )

    print(
        "─" * 70
    )

    if not schedule:

        print(
            "No episode schedule available."
        )

        print()

        print(
    "Schedule data: Tsuzuki"
)

        print(
    "Metadata source: AniList"
)

        return

    grouped = {}

    for item in schedule:

        episode = item.get(
            "episode"
        )

        grouped.setdefault(
            episode,
            [],
        ).append(
            item
        )

    for episode in sorted(
        grouped,
        key=lambda value: (
            value
            if value is not None
            else 9999
        ),
    ):

        print()

        if episode is None:

            print(
                "Episode TBA"
            )

        else:

            print(
                f"Episode {episode}"
            )

        for item in grouped[
            episode
        ]:

            air_type = (
                item.get(
                    "airType"
                )
                or "release"
            ).upper()

            if item.get(
                "isBreak"
            ):

                line = (
                    f"  {air_type:<5} "
                    f"BREAK"
                )

                note = print_tsuzuki_note(
                    item.get(
                        "note"
                    )
                )

                if note:

                    line += (
                        f" | {note}"
                    )

                print(
                    line
                )

                continue

            airing_at = item.get(
                "airingAt"
            )

            if airing_at:

                local_time = (
                    datetime.fromtimestamp(
                        airing_at
                    ).astimezone()
                )

                time_text = (
                    local_time.strftime(
                        "%a, %b %d, %Y "
                        "at %I:%M %p %Z"
                    )
                )

            else:

                time_text = "TBA"

            estimated = (
                item.get(
                    "estimated"
                )
            )

            marker = (
                "~"
                if estimated
                else ""
            )

            line = (
                f"  {marker}"
                f"{air_type:<5} "
                f"{time_text}"
            )

            platform = item.get(
                "platform"
            )

            if air_type == "SUB":

                platform = "Amazon Prime Video"

            if platform:

                line += (
                    f" | {platform}"
                )

            note = print_tsuzuki_note(
                item.get(
                    "note"
                )
            )

            if note:

                line += (
                    f" | {note}"
                )

            print(
                line
            )

    print()

    print(
        "Schedule data: Tsuzuki"
    )

    print(
        "Metadata source: AniList"
    )



def main():

    parser = argparse.ArgumentParser(
        prog="ani"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=(
            f"Anime Release CLI "
            f"{get_cli_version()}"
        ),
    )

    sub = parser.add_subparsers(
        dest="command"
    )

    search = sub.add_parser(
        "search"
    )

    search.add_argument(
        "title",
        nargs="+",
    )

    info = sub.add_parser(
        "info"
    )

    info.add_argument(
        "title",
        nargs="+",
    )

    schedule = sub.add_parser(
        "schedule"
    )

    schedule.add_argument(
        "title",
        nargs="+",
    )

    airing = sub.add_parser(
        "airing"
    )

    airing.add_argument(
        "title",
        nargs="+",
    )

    relations = sub.add_parser(
        "relations"
    )

    relations.add_argument(
        "title",
        nargs="+",
    )

    studio = sub.add_parser(
        "studio"
    )

    studio.add_argument(
        "name"
    )

    season = sub.add_parser(
        "season"
    )

    season.add_argument(
        "season"
    )

    season.add_argument(
        "--studio"
    )

    sub.add_parser(
        "upcoming"
    )

    sub.add_parser(
        "yesterday"
    )

    sub.add_parser(
        "today"
    )

    sub.add_parser(
        "tomorrow"
    )

    args = parser.parse_args()

    try:

        if args.command == "search":

            handle_search(
                " ".join(
                    args.title
                )
            )

        elif args.command == "info":

            handle_info(
                " ".join(
                    args.title
                )
            )

        elif args.command == "schedule":

            handle_schedule(
                " ".join(
                    args.title
                )
            )

        elif args.command == "airing":

            handle_airing(
                " ".join(
                    args.title
                )
            )

        elif args.command == "relations":

            handle_relations(
                " ".join(
                    args.title
                )
            )

        elif args.command == "studio":

            handle_studio(
                args.name
            )

        elif args.command == "season":

            handle_season(
                args.season,
                args.studio,
            )

        elif args.command == "upcoming":

            handle_upcoming()

        elif args.command == "yesterday":

            handle_yesterday()

        elif args.command == "today":

            handle_today()

        elif args.command == "tomorrow":

            handle_tomorrow()

        else:

            parser.print_help()

    except (
        AniListAPIError,
        KitsuAPIError,
        TsuzukiAPIError,
    ) as error:

        print()

        print(
            f"Error: {error}"
        )


if __name__ == "__main__":

    main()