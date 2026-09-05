import os
import requests

from datetime import (
    datetime,
    timedelta,
)


ANILIST_API_URL = "https://graphql.anilist.co"
KITSU_API_URL = "https://kitsu.io/api/edge"
TSUZUKI_API_URL = "https://tsuzuki.top/api/v1"
ANIMESCHEDULE_API_URL = "https://animeschedule.net/api/v3"


class AniListAPIError(Exception):
    """Raised when the AniList API cannot complete a request."""

    pass


class KitsuAPIError(Exception):
    """Raised when the Kitsu API cannot complete a request."""

    pass


class TsuzukiAPIError(Exception):
    """Raised when the Tsuzuki API cannot complete a request."""

    pass


class AnimeScheduleAPIError(Exception):
    """Raised when AnimeSchedule cannot complete a request."""

    pass


ENTRIES_QUERY = """
query ($search: String) {

  Page(
    page: 1,
    perPage: 10
  ) {

    media(
      search: $search,
      type: ANIME,
      sort: SEARCH_MATCH
    ) {

      id

      title {
        romaji
        english
      }

      coverImage {
        extraLarge
        large
        medium
      }

      description(asHtml: false)

      status
      episodes
      format
      source

      season
      seasonYear

      startDate {
        year
        month
        day
      }

      endDate {
        year
        month
        day
      }

      genres

      studios(isMain:true) {

        nodes {
          name
        }

      }

      nextAiringEpisode {

        episode
        airingAt
        timeUntilAiring

      }

    }

  }

}
"""


RELATIONS_QUERY = """
query ($id: Int) {

  Media(
    id: $id,
    type: ANIME
  ) {

    id

    title {
      romaji
      english
    }

    relations {

      edges {

        relationType

        node {

          id
          type
          format
          status
          episodes

          title {
            romaji
            english
          }

          season
          seasonYear

        }

      }

    }

  }

}
"""


ALL_ANIME_QUERY = """
query ($page:Int, $perPage:Int) {

  Page(
    page:$page,
    perPage:$perPage
  ) {

    media(

      type: ANIME,
      sort: POPULARITY_DESC

    ) {

      id

      title {

        romaji
        english

      }

      status
      episodes
      format

      studios(isMain:true) {

        nodes {

          name

        }

      }

    }

  }

}
"""


SEASON_QUERY = """
query ($season:MediaSeason, $year:Int) {

  Page(
    page:1,
    perPage:50
  ) {

    media(

      type:ANIME,
      season:$season,
      seasonYear:$year

    ) {

      id

      title {

        romaji
        english

      }

      status
      episodes
      format
      source

      season
      seasonYear

      startDate {
        year
        month
        day
      }

      endDate {
        year
        month
        day
      }

      genres

      studios(isMain:true) {

        nodes {

          name

        }

      }

      nextAiringEpisode {

        episode
        airingAt
        timeUntilAiring

      }

    }

  }

}
"""


UPCOMING_QUERY = """
query {

  Page(
    page:1,
    perPage:20
  ) {

    media(

      type:ANIME,
      status:NOT_YET_RELEASED,
      sort:START_DATE

    ) {

      id

      title {

        romaji
        english

      }

      status
      episodes
      format

      startDate {

        year
        month
        day

      }

    }

  }

}
"""


AIRING_QUERY = """
query ($start:Int,$end:Int) {

  Page(
    page:1,
    perPage:50
  ) {

    airingSchedules(

      airingAt_greater:$start,
      airingAt_lesser:$end

    ) {

      airingAt

      episode

      media {

        title {

          romaji
          english

        }

      }

    }

  }

}
"""


def send_query(query, variables=None):

    try:

        response = requests.post(
            ANILIST_API_URL,
            json={
                "query": query,
                "variables": variables or {},
            },
            timeout=15,
        )

    except requests.exceptions.Timeout as exc:

        raise AniListAPIError(
            "AniList request timed out."
        ) from exc

    except requests.exceptions.ConnectionError as exc:

        raise AniListAPIError(
            "Unable to connect to AniList."
        ) from exc

    except requests.exceptions.RequestException as exc:

        raise AniListAPIError(
            "Unable to complete the AniList request."
        ) from exc

    if response.status_code == 403:

        try:

            error_data = response.json()

            errors = error_data.get(
                "errors",
                [],
            )

            if errors:

                message = errors[0].get(
                    "message"
                )

                if message:

                    raise AniListAPIError(
                        message
                    )

        except ValueError:

            pass

        raise AniListAPIError(
            "AniList API returned HTTP 403 Forbidden."
        )

    if response.status_code == 429:

        raise AniListAPIError(
            "AniList API rate limit reached."
        )

    if response.status_code >= 500:

        raise AniListAPIError(
            f"AniList is currently unavailable "
            f"(HTTP {response.status_code})."
        )

    try:

        response.raise_for_status()

    except requests.exceptions.HTTPError as exc:

        raise AniListAPIError(
            f"AniList API request failed "
            f"(HTTP {response.status_code})."
        ) from exc

    try:

        data = response.json()

    except ValueError as exc:

        raise AniListAPIError(
            "AniList returned an invalid response."
        ) from exc

    if data.get("errors"):

        message = data["errors"][0].get(
            "message",
            "Unknown AniList API error.",
        )

        raise AniListAPIError(
            message
        )

    if "data" not in data:

        raise AniListAPIError(
            "AniList returned an unexpected response."
        )

    return data["data"]


def send_kitsu_request(
    endpoint,
    params=None,
):

    url = (
        f"{KITSU_API_URL}"
        f"{endpoint}"
    )

    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "User-Agent": "Anime-Release-CLI/1.2.1",
    }

    try:

        response = requests.get(
            url,
            params=params or {},
            headers=headers,
            timeout=15,
        )

    except requests.exceptions.Timeout as exc:

        raise KitsuAPIError(
            "Kitsu request timed out."
        ) from exc

    except requests.exceptions.ConnectionError as exc:

        raise KitsuAPIError(
            "Unable to connect to Kitsu."
        ) from exc

    except requests.exceptions.RequestException as exc:

        raise KitsuAPIError(
            "Unable to complete the Kitsu request."
        ) from exc

    if response.status_code == 429:

        raise KitsuAPIError(
            "Kitsu rate limit reached."
        )

    if response.status_code >= 500:

        raise KitsuAPIError(
            f"Kitsu is currently unavailable "
            f"(HTTP {response.status_code})."
        )

    try:

        response.raise_for_status()

    except requests.exceptions.HTTPError as exc:

        raise KitsuAPIError(
            f"Kitsu request failed "
            f"(HTTP {response.status_code})."
        ) from exc

    try:

        return response.json()

    except ValueError as exc:

        raise KitsuAPIError(
            "Kitsu returned an invalid response."
        ) from exc


def send_tsuzuki_request(
    endpoint,
    params=None,
):

    url = (
        f"{TSUZUKI_API_URL}"
        f"{endpoint}"
    )

    headers = {
        "Accept": "application/json",
        "User-Agent": "Anime-Release-CLI/1.2.1",
    }

    try:

        response = requests.get(
            url,
            params=params or {},
            headers=headers,
            timeout=15,
        )

    except requests.exceptions.Timeout as exc:

        raise TsuzukiAPIError(
            "Tsuzuki request timed out."
        ) from exc

    except requests.exceptions.ConnectionError as exc:

        raise TsuzukiAPIError(
            "Unable to connect to Tsuzuki."
        ) from exc

    except requests.exceptions.RequestException as exc:

        raise TsuzukiAPIError(
            "Unable to complete the Tsuzuki request."
        ) from exc

    if response.status_code == 400:

        try:

            error_data = response.json()

            error_message = error_data.get(
                "error"
            )

            hint = error_data.get(
                "hint"
            )

            if error_message:

                message = (
                    f"Tsuzuki rejected the request: "
                    f"{error_message}"
                )

                if hint:

                    message += (
                        f" Hint: {hint}"
                    )

                raise TsuzukiAPIError(
                    message
                )

        except ValueError:

            pass

        raise TsuzukiAPIError(
            "Tsuzuki rejected the request "
            "(HTTP 400)."
        )

    if response.status_code == 404:

        raise TsuzukiAPIError(
            "Anime not found in Tsuzuki."
        )

    if response.status_code == 429:

        raise TsuzukiAPIError(
            "Tsuzuki rate limit reached."
        )

    if response.status_code >= 500:

        raise TsuzukiAPIError(
            f"Tsuzuki is currently unavailable "
            f"(HTTP {response.status_code})."
        )

    try:

        response.raise_for_status()

    except requests.exceptions.HTTPError as exc:

        raise TsuzukiAPIError(
            f"Tsuzuki request failed "
            f"(HTTP {response.status_code})."
        ) from exc

    try:

        data = response.json()

    except ValueError as exc:

        raise TsuzukiAPIError(
            "Tsuzuki returned an invalid response."
        ) from exc

    if data.get("ok") is False:

        message = data.get(
            "error",
            "Tsuzuki returned an error.",
        )

        hint = data.get(
            "hint"
        )

        if hint:

            message = (
                f"{message} "
                f"Hint: {hint}"
            )

        raise TsuzukiAPIError(
            message
        )

    return data


def send_animeschedule_request(
    endpoint,
    params=None,
):

    url = (
        f"{ANIMESCHEDULE_API_URL}"
        f"{endpoint}"
    )

    headers = {
        "Accept": "application/json",
        "User-Agent": "Anime-Release-CLI/1.2.1",
    }

    token = os.environ.get(
        "ANIMESCHEDULE_TOKEN"
    )

    if token:

        headers[
            "Authorization"
        ] = f"Bearer {token}"

    try:

        response = requests.get(
            url,
            params=params or {},
            headers=headers,
            timeout=20,
        )

    except requests.exceptions.Timeout as exc:

        raise AnimeScheduleAPIError(
            "AnimeSchedule request timed out."
        ) from exc

    except requests.exceptions.ConnectionError as exc:

        raise AnimeScheduleAPIError(
            "Unable to connect to AnimeSchedule."
        ) from exc

    except requests.exceptions.RequestException as exc:

        raise AnimeScheduleAPIError(
            "Unable to complete the "
            "AnimeSchedule request."
        ) from exc

    if response.status_code == 401:

        raise AnimeScheduleAPIError(
            "AnimeSchedule rejected the "
            "API authorization."
        )

    if response.status_code == 403:

        raise AnimeScheduleAPIError(
            "AnimeSchedule denied the request."
        )

    if response.status_code == 429:

        raise AnimeScheduleAPIError(
            "AnimeSchedule rate limit reached."
        )

    if response.status_code >= 500:

        raise AnimeScheduleAPIError(
            f"AnimeSchedule is currently unavailable "
            f"(HTTP {response.status_code})."
        )

    try:

        response.raise_for_status()

    except requests.exceptions.HTTPError as exc:

        raise AnimeScheduleAPIError(
            f"AnimeSchedule request failed "
            f"(HTTP {response.status_code})."
        ) from exc

    try:

        return response.json()

    except ValueError as exc:

        raise AnimeScheduleAPIError(
            "AnimeSchedule returned an "
            "invalid response."
        ) from exc


def parse_kitsu_date(value):

    if not value:

        return {
            "year": None,
            "month": None,
            "day": None,
        }

    try:

        date = datetime.strptime(
            value,
            "%Y-%m-%d",
        )

        return {
            "year": date.year,
            "month": date.month,
            "day": date.day,
        }

    except ValueError:

        return {
            "year": None,
            "month": None,
            "day": None,
        }


def parse_kitsu_datetime(value):

    if not value:

        return None

    try:

        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

    except ValueError:

        return None


def normalize_kitsu_status(status):

    if not status:

        return None

    status_map = {
        "current": "RELEASING",
        "finished": "FINISHED",
        "tba": "NOT_YET_RELEASED",
        "unreleased": "NOT_YET_RELEASED",
        "upcoming": "NOT_YET_RELEASED",
    }

    return status_map.get(
        status.lower(),
        status.upper().replace(
            " ",
            "_",
        ),
    )


def normalize_kitsu_format(subtype):

    if not subtype:

        return None

    format_map = {
        "TV": "TV",
        "tv": "TV",
        "movie": "MOVIE",
        "Movie": "MOVIE",
        "OVA": "OVA",
        "ova": "OVA",
        "ONA": "ONA",
        "ona": "ONA",
        "special": "SPECIAL",
        "Special": "SPECIAL",
        "music": "MUSIC",
        "Music": "MUSIC",
    }

    return format_map.get(
        subtype,
        subtype.upper().replace(
            " ",
            "_",
        ),
    )


def determine_season(start_date):

    if not start_date:

        return None

    month = start_date.get(
        "month"
    )

    if not month:

        return None

    if month in (
        1,
        2,
        3,
    ):

        return "WINTER"

    if month in (
        4,
        5,
        6,
    ):

        return "SPRING"

    if month in (
        7,
        8,
        9,
    ):

        return "SUMMER"

    return "FALL"


def build_kitsu_next_airing(
    attributes,
):

    next_release = attributes.get(
        "nextRelease"
    )

    release_datetime = parse_kitsu_datetime(
        next_release
    )

    if not release_datetime:

        return None

    now = datetime.now(
        release_datetime.tzinfo
    )

    seconds = int(
        (
            release_datetime
            - now
        ).total_seconds()
    )

    if seconds < 0:

        seconds = 0

    return {
        "episode": None,

        "airingAt": int(
            release_datetime.timestamp()
        ),

        "timeUntilAiring": seconds,
    }


def normalize_kitsu_anime(
    anime,
):

    attributes = anime.get(
        "attributes",
        {},
    )

    titles = (
        attributes.get(
            "titles",
            {},
        )
        or {}
    )

    poster_image = (
        attributes.get(
            "posterImage",
            {},
        )
        or {}
    )

    start_date = parse_kitsu_date(
        attributes.get(
            "startDate"
        )
    )

    end_date = parse_kitsu_date(
        attributes.get(
            "endDate"
        )
    )

    canonical_title = (
        attributes.get(
            "canonicalTitle"
        )
        or titles.get(
            "en_jp"
        )
        or titles.get(
            "ja_jp"
        )
        or "Unknown"
    )

    english_title = (
        titles.get("en")
        or titles.get("en_us")
    )

    year = start_date.get(
        "year"
    )

    return {
        "id": anime.get(
            "id"
        ),

        "_provider": "kitsu",

        "title": {
            "romaji": canonical_title,
            "english": english_title,
        },

        "coverImage": {
            "extraLarge": poster_image.get(
                "original"
            ),
            "large": poster_image.get(
                "large"
            ),
            "medium": poster_image.get(
                "medium"
            ),
            "small": poster_image.get(
                "small"
            ),
            "original": poster_image.get(
                "original"
            ),
        },

        "status": normalize_kitsu_status(
            attributes.get(
                "status"
            )
        ),

        "episodes": attributes.get(
            "episodeCount"
        ),

        "format": normalize_kitsu_format(
            attributes.get(
                "subtype"
            )
        ),

        "source": None,

        "season": determine_season(
            start_date
        ),

        "seasonYear": year,

        "startDate": start_date,

        "endDate": end_date,

        "genres": [],

        "studios": {
            "nodes": []
        },

        "nextAiringEpisode": (
            build_kitsu_next_airing(
                attributes
            )
        ),

        "description": (
            attributes.get(
                "synopsis"
            )
            or attributes.get(
                "description"
            )
        ),

        "_popularityRank": attributes.get(
            "popularityRank"
        ),

        "_ratingRank": attributes.get(
            "ratingRank"
        ),
    }


def mark_anilist_provider(
    entries,
):

    for anime in entries:

        anime[
            "_provider"
        ] = "anilist"

    return entries


def get_kitsu_anime_entries(
    title,
):

    results = []
    seen_ids = set()

    page_limit = 20
    max_pages = 5

    for page in range(
        max_pages
    ):

        offset = (
            page
            * page_limit
        )

        data = send_kitsu_request(
            "/anime",
            {
                "filter[text]": title,
                "page[limit]": page_limit,
                "page[offset]": offset,
            },
        )

        page_results = data.get(
            "data",
            [],
        )

        if not page_results:

            break

        for anime in page_results:

            anime_id = anime.get(
                "id"
            )

            if anime_id in seen_ids:

                continue

            if anime_id is not None:

                seen_ids.add(
                    anime_id
                )

            results.append(
                normalize_kitsu_anime(
                    anime
                )
            )

        if len(
            page_results
        ) < page_limit:

            break

    def sort_key(
        anime,
    ):

        status = anime.get(
            "status"
        )

        if status == "RELEASING":

            status_priority = 0

        elif status == "NOT_YET_RELEASED":

            status_priority = 1

        else:

            status_priority = 2

        year = (
            anime.get(
                "seasonYear"
            )
            or 0
        )

        popularity = (
            anime.get(
                "_popularityRank"
            )
            or 999999
        )

        return (
            status_priority,
            -year,
            popularity,
        )

    results.sort(
        key=sort_key
    )

    return results


def get_anime_entries(title):

    try:

        data = send_query(
            ENTRIES_QUERY,
            {
                "search": title,
            },
        )

        return mark_anilist_provider(
            data[
                "Page"
            ][
                "media"
            ]
        )

    except AniListAPIError as anilist_error:

        try:

            entries = get_kitsu_anime_entries(
                title
            )

            if entries:

                return entries

        except KitsuAPIError as kitsu_error:

            raise AniListAPIError(
                f"AniList unavailable: "
                f"{anilist_error} "
                f"Kitsu fallback also failed: "
                f"{kitsu_error}"
            ) from kitsu_error

        raise AniListAPIError(
            f"AniList unavailable: "
            f"{anilist_error} "
            "Kitsu fallback returned "
            "no matching anime."
        )


def get_anime_relations(
    anime_id,
    provider="anilist",
):

    if provider == "kitsu":

        return []

    data = send_query(
        RELATIONS_QUERY,
        {
            "id": anime_id,
        },
    )

    media = data.get(
        "Media"
    )

    if not media:

        return []

    relations = media.get(
        "relations",
        {},
    )

    return relations.get(
        "edges",
        [],
    )


def get_studio_anime(studio):

    results = []

    for page in range(
        1,
        6,
    ):

        data = send_query(
            ALL_ANIME_QUERY,
            {
                "page": page,
                "perPage": 50,
            },
        )

        for anime in data[
            "Page"
        ][
            "media"
        ]:

            studios = [
                item[
                    "name"
                ].lower()

                for item in anime.get(
                    "studios",
                    {},
                ).get(
                    "nodes",
                    [],
                )
            ]

            if studio.lower() in studios:

                anime[
                    "_provider"
                ] = "anilist"

                results.append(
                    anime
                )

    return results


def get_kitsu_season(
    season,
    year,
):

    data = send_kitsu_request(
        "/anime",
        {
            "filter[season]": season.lower(),
            "filter[seasonYear]": year,
            "page[limit]": 20,
            "sort": "popularityRank",
        },
    )

    normalized = [
        normalize_kitsu_anime(
            anime
        )
        for anime in data.get(
            "data",
            [],
        )
    ]

    requested_season = (
        season.upper()
    )

    return [
        anime

        for anime in normalized

        if (
            anime.get(
                "season"
            )
            == requested_season

            and anime.get(
                "seasonYear"
            )
            == year
        )
    ]


def get_anime_season(
    season,
    year,
):

    try:

        data = send_query(
            SEASON_QUERY,
            {
                "season": (
                    season.upper()
                ),
                "year": year,
            },
        )

        return mark_anilist_provider(
            data[
                "Page"
            ][
                "media"
            ]
        )

    except AniListAPIError as anilist_error:

        try:

            entries = get_kitsu_season(
                season,
                year,
            )

            if entries:

                return entries

        except KitsuAPIError as kitsu_error:

            raise AniListAPIError(
                f"AniList unavailable: "
                f"{anilist_error} "
                f"Kitsu season fallback also failed: "
                f"{kitsu_error}"
            ) from kitsu_error

        raise AniListAPIError(
            f"AniList unavailable: "
            f"{anilist_error} "
            "Kitsu returned no anime "
            "for that season."
        )


def get_kitsu_upcoming():

    data = send_kitsu_request(
        "/anime",
        {
            "filter[status]": "upcoming",
            "page[limit]": 20,
            "sort": "startDate",
        },
    )

    entries = [
        normalize_kitsu_anime(
            anime
        )
        for anime in data.get(
            "data",
            [],
        )
    ]

    entries.sort(
        key=lambda anime: (
            anime.get(
                "startDate",
                {},
            ).get(
                "year"
            )
            or 9999,

            anime.get(
                "startDate",
                {},
            ).get(
                "month"
            )
            or 12,

            anime.get(
                "startDate",
                {},
            ).get(
                "day"
            )
            or 31,
        )
    )

    return entries


def get_upcoming_anime():

    try:

        data = send_query(
            UPCOMING_QUERY
        )

        return mark_anilist_provider(
            data[
                "Page"
            ][
                "media"
            ]
        )

    except AniListAPIError as anilist_error:

        try:

            entries = get_kitsu_upcoming()

            if entries:

                return entries

        except KitsuAPIError as kitsu_error:

            raise AniListAPIError(
                f"AniList unavailable: "
                f"{anilist_error} "
                f"Kitsu upcoming fallback also failed: "
                f"{kitsu_error}"
            ) from kitsu_error

        raise AniListAPIError(
            f"AniList unavailable: "
            f"{anilist_error} "
            "Kitsu returned no upcoming anime."
        )


def local_day_bounds(
    days_from_today=0,
):

    now = datetime.now().astimezone()

    target = (
        now
        + timedelta(
            days=days_from_today
        )
    )

    start = target.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end = (
        start
        + timedelta(
            days=1
        )
    )

    return (
        start,
        end,
    )


def get_anilist_airing_day(
    days_from_today=0,
):

    start, end = local_day_bounds(
        days_from_today
    )

    data = send_query(
        AIRING_QUERY,
        {
            "start": int(
                start.timestamp()
            ),
            "end": int(
                end.timestamp()
            ),
        },
    )

    schedules = data[
        "Page"
    ][
        "airingSchedules"
    ]

    for item in schedules:

        item[
            "_provider"
        ] = "anilist"

    return schedules


def normalize_tsuzuki_schedule(
    episode,
):

    title = (
        episode.get(
            "title"
        )
        or "Unknown Anime"
    )

    return {
        "airingAt": episode.get(
            "airingAt"
        ),

        "episode": episode.get(
            "episode"
        ),

        "media": {
            "title": {
                "romaji": title,
                "english": title,
            }
        },

        "_provider": "tsuzuki",

        "airType": episode.get(
            "airType"
        ),

        "platform": episode.get(
            "platform"
        ),

        "exact": episode.get(
            "exact"
        ),

        "estimated": episode.get(
            "estimated"
        ),

        "isBreak": episode.get(
            "isBreak"
        ),

        "note": episode.get(
            "note"
        ),
    }


def get_tsuzuki_airing_day(
    days_from_today=0,
):

    start, end = local_day_bounds(
        days_from_today
    )

    query_start = (
        start
        - timedelta(
            days=1
        )
    )

    data = send_tsuzuki_request(
        "/schedule",
        {
            "start": query_start.strftime(
                "%Y-%m-%d"
            ),
            "days": 3,
        },
    )

    schedules = []

    for episode in data.get(
        "episodes",
        [],
    ):

        airing_at = episode.get(
            "airingAt"
        )

        if not airing_at:

            continue

        local_airing_time = (
            datetime.fromtimestamp(
                airing_at,
                tz=start.tzinfo,
            )
        )

        if not (
            start
            <= local_airing_time
            < end
        ):

            continue

        if episode.get(
            "isBreak"
        ):

            continue

        schedules.append(
            normalize_tsuzuki_schedule(
                episode
            )
        )

    schedules.sort(
        key=lambda item: (
            item.get(
                "airingAt"
            )
            or 0
        )
    )

    return schedules


def parse_animeschedule_datetime(
    value,
):

    if not value:

        return None

    if value.startswith(
        "0001-01-01"
    ):

        return None

    try:

        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def get_animeschedule_platform(
    streams,
):

    if not streams:

        return None

    if isinstance(
        streams,
        dict,
    ):

        platform = (
            streams.get(
                "name"
            )
            or streams.get(
                "platform"
            )
        )

        return platform

    if isinstance(
        streams,
        list,
    ):

        for stream in streams:

            if not isinstance(
                stream,
                dict,
            ):

                continue

            platform = (
                stream.get(
                    "name"
                )
                or stream.get(
                    "platform"
                )
            )

            if platform:

                return platform

    return None


def normalize_animeschedule_entry(
    entry,
):

    romaji = (
        entry.get(
            "romaji"
        )
        or entry.get(
            "title"
        )
        or entry.get(
            "english"
        )
        or "Unknown Anime"
    )

    english = (
        entry.get(
            "english"
        )
        or entry.get(
            "title"
        )
        or romaji
    )

    episode_date = (
        parse_animeschedule_datetime(
            entry.get(
                "episodeDate"
            )
        )
    )

    if not episode_date:

        return None

    air_type = (
        entry.get(
            "airType"
        )
        or ""
    )

    if air_type:

        air_type = (
            air_type.upper()
        )

    return {
        "airingAt": int(
            episode_date.timestamp()
        ),

        "episode": entry.get(
            "episodeNumber"
        ),

        "media": {
            "title": {
                "romaji": romaji,
                "english": english,
            }
        },

        "_provider": "animeschedule",

        "airType": air_type,

        "platform": (
            get_animeschedule_platform(
                entry.get(
                    "streams"
                )
            )
        ),

        "exact": True,

        "estimated": False,

        "isBreak": False,

        "note": entry.get(
            "delayedText"
        ),

        "route": entry.get(
            "route"
        ),

        "airingStatus": entry.get(
            "airingStatus"
        ),
    }


def get_animeschedule_airing_day(
    days_from_today=0,
):

    start, end = local_day_bounds(
        days_from_today
    )

    target_date = (
        start.date()
    )

    iso_calendar = (
        target_date.isocalendar()
    )

    data = send_animeschedule_request(
        "/timetables",
        {
            "year": iso_calendar.year,
            "week": iso_calendar.week,
        },
    )

    if isinstance(
        data,
        dict,
    ):

        entries = (
            data.get(
                "data"
            )
            or data.get(
                "timetables"
            )
            or data.get(
                "anime"
            )
            or []
        )

    elif isinstance(
        data,
        list,
    ):

        entries = data

    else:

        raise AnimeScheduleAPIError(
            "AnimeSchedule returned an "
            "unexpected timetable response."
        )

    schedules = []

    seen = set()

    for entry in entries:

        if not isinstance(
            entry,
            dict,
        ):

            continue

        normalized = (
            normalize_animeschedule_entry(
                entry
            )
        )

        if not normalized:

            continue

        airing_at = normalized.get(
            "airingAt"
        )

        if not airing_at:

            continue

        local_airing_time = (
            datetime.fromtimestamp(
                airing_at,
                tz=start.tzinfo,
            )
        )

        if not (
            start
            <= local_airing_time
            < end
        ):

            continue

        key = (
            normalized.get(
                "airingAt"
            ),
            normalized.get(
                "episode"
            ),
            normalized.get(
                "airType"
            ),
            normalized.get(
                "media",
                {},
            ).get(
                "title",
                {},
            ).get(
                "romaji"
            ),
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        schedules.append(
            normalized
        )

    schedules.sort(
        key=lambda item: (
            item.get(
                "airingAt"
            )
            or 0
        )
    )

    return schedules

def deduplicate_schedule_entries(
    schedules,
):

    deduplicated = {}

    for item in schedules:

        media = item.get(
            "media",
            {},
        )

        media_id = media.get(
            "id"
        )

        title_data = media.get(
            "title",
            {},
        )

        title = (
            title_data.get(
                "english"
            )
            or title_data.get(
                "romaji"
            )
            or title_data.get(
                "native"
            )
            or "Unknown Anime"
        )

        # Prefer the provider's anime ID so different
        # episodes of the same anime are recognized
        # as belonging to the same series.
        if media_id is not None:
            key = (
                "id",
                media_id,
            )
        else:
            key = (
                "title",
                title.strip().lower(),
            )

        existing = deduplicated.get(
            key
        )

        if existing is None:

            deduplicated[
                key
            ] = item

            continue

        existing_episode = existing.get(
            "episode"
        )

        new_episode = item.get(
            "episode"
        )

        # Keep the newest / highest episode number.
        if (
            new_episode is not None
            and (
                existing_episode is None
                or new_episode
                > existing_episode
            )
        ):

            deduplicated[
                key
            ] = item

            continue

        # If both entries are for the same episode,
        # keep the earliest airing time.
        if (
            new_episode
            == existing_episode
        ):

            existing_airing = (
                existing.get(
                    "airingAt"
                )
                or 9999999999
            )

            new_airing = (
                item.get(
                    "airingAt"
                )
                or 9999999999
            )

            if (
                new_airing
                < existing_airing
            ):

                deduplicated[
                    key
                ] = item

    results = list(
        deduplicated.values()
    )

    results.sort(
        key=lambda item: (
            item.get(
                "airingAt"
            )
            or 0
        )
    )

    return results

def get_schedule_with_fallback(
    days_from_today,
):

    anilist_error_message = None
    tsuzuki_error_message = None
    animeschedule_error_message = None

    try:

        schedules = (
            get_anilist_airing_day(
                days_from_today
            )
        )

        if schedules:

            return deduplicate_schedule_entries(
                schedules
            )

        anilist_error_message = (
            "AniList returned no "
            "schedule entries."
        )

    except AniListAPIError as error:

        anilist_error_message = str(
            error
        )

    try:

        schedules = (
            get_tsuzuki_airing_day(
                days_from_today
            )
        )

        if schedules:

            return deduplicate_schedule_entries(
                schedules
            )

        tsuzuki_error_message = (
            "Tsuzuki returned no "
            "schedule entries."
        )

    except TsuzukiAPIError as error:

        tsuzuki_error_message = str(
            error
        )

    try:

        schedules = (
            get_animeschedule_airing_day(
                days_from_today
            )
        )

        if schedules:

            return deduplicate_schedule_entries(
                schedules
            )

        animeschedule_error_message = (
            "AnimeSchedule returned no "
            "schedule entries."
        )

    except AnimeScheduleAPIError as error:

        animeschedule_error_message = str(
            error
        )

    raise AniListAPIError(
        f"AniList unavailable: "
        f"{anilist_error_message} "
        f"Tsuzuki schedule fallback "
        f"also failed: "
        f"{tsuzuki_error_message} "
        f"AnimeSchedule fallback "
        f"also failed: "
        f"{animeschedule_error_message}"
    )


def get_anime_airing_yesterday():

    return get_schedule_with_fallback(
        -1
    )


def get_anime_airing_today():

    return get_schedule_with_fallback(
        0
    )


def get_anime_airing_tomorrow():

    return get_schedule_with_fallback(
        1
    )


def get_tsuzuki_airing_matches(
    title,
):

    data = send_tsuzuki_request(
        "/search",
        {
            "q": title,
            "limit": 25,
        },
    )

    entries = data.get(
        "anime",
        [],
    )

    if not entries:

        return []

    releasing = [
        anime
        for anime in entries
        if anime.get(
            "status"
        ) == "RELEASING"
    ]

    if releasing:

        return releasing

    return entries


def collect_tsuzuki_episode_entries(
    value,
):

    collected = []

    if isinstance(
        value,
        dict,
    ):

        if (
            "episode" in value
            and (
                "airType" in value
                or "airingAt" in value
                or "isBreak" in value
            )
        ):

            collected.append(
                value
            )

        for child in value.values():

            collected.extend(
                collect_tsuzuki_episode_entries(
                    child
                )
            )

    elif isinstance(
        value,
        list,
    ):

        for child in value:

            collected.extend(
                collect_tsuzuki_episode_entries(
                    child
                )
            )

    return collected


def get_tsuzuki_anime_schedule(
    anilist_id,
):

    data = send_tsuzuki_request(
        f"/anime/{anilist_id}"
    )

    raw_entries = (
        collect_tsuzuki_episode_entries(
            data
        )
    )

    seen = set()
    entries = []

    for item in raw_entries:

        key = (
            item.get(
                "episode"
            ),
            item.get(
                "airType"
            ),
            item.get(
                "airingAt"
            ),
            item.get(
                "platform"
            ),
            item.get(
                "isBreak"
            ),
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        entries.append(
            {
                "episode": item.get(
                    "episode"
                ),

                "airType": item.get(
                    "airType"
                ),

                "airingAt": item.get(
                    "airingAt"
                ),

                "airingAtIso": item.get(
                    "airingAtIso"
                ),

                "platform": item.get(
                    "platform"
                ),

                "exact": item.get(
                    "exact"
                ),

                "estimated": item.get(
                    "estimated"
                ),

                "isBreak": item.get(
                    "isBreak",
                    False,
                ),

                "note": item.get(
                    "note"
                ),
            }
        )

    entries.sort(
        key=lambda item: (
            item.get(
                "episode"
            )
            if item.get(
                "episode"
            ) is not None
            else 9999,

            item.get(
                "airingAt"
            )
            if item.get(
                "airingAt"
            ) is not None
            else 9999999999,

            item.get(
                "airType"
            )
            or "",
        )
    )

    return entries