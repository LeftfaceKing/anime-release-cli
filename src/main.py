import argparse
import base64
import html
import os
import re
import shutil
import subprocess
import sys
import textwrap

from datetime import datetime

from importlib.metadata import (
    version,
    PackageNotFoundError,
)

from pathlib import Path

from urllib.parse import urlparse

import requests

from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
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


GREEN = "\033[38;2;102;255;0m"
WHITE = "\033[38;2;235;235;235m"
DIM = "\033[38;2;135;135;135m"
RESET = "\033[0m"


def get_cli_version():

    try:

        return version(
            "anime-release-cli"
        )

    except PackageNotFoundError:

        return "1.3.0"


def anime_title(anime):

    title_data = anime.get(
        "title",
        {},
    )

    return (
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


def provider_name(anime):

    provider = anime.get(
        "_provider"
    )

    if provider == "kitsu":

        return "Kitsu"

    if provider == "tsuzuki":

        return "Tsuzuki"

    if provider == "animeschedule":

        return "AnimeSchedule"

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

    elif provider == "animeschedule":

        print()

        print(
            "AniList and Tsuzuki are unavailable. "
            "Using AnimeSchedule fallback."
        )


# ============================================================
# COVER IMAGE
# ============================================================


def get_cover_image_url(
    anime,
):

    cover_image = anime.get(
        "coverImage"
    )

    if not isinstance(
        cover_image,
        dict,
    ):

        return None

    return (
        cover_image.get(
            "extraLarge"
        )
        or cover_image.get(
            "large"
        )
        or cover_image.get(
            "original"
        )
        or cover_image.get(
            "medium"
        )
        or cover_image.get(
            "small"
        )
    )


def get_cover_cache_directory():

    cache_directory = (
        Path.home()
        / "Library"
        / "Caches"
        / "anime-release-cli"
        / "covers"
    )

    cache_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return cache_directory


def safe_cover_filename(
    anime,
    image_url,
):

    anime_id = (
        anime.get(
            "id"
        )
        or "anime"
    )

    provider = (
        anime.get(
            "_provider"
        )
        or "anilist"
    )

    parsed_url = urlparse(
        image_url
    )

    suffix = Path(
        parsed_url.path
    ).suffix.lower()

    valid_suffixes = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    if suffix not in valid_suffixes:

        suffix = ".jpg"

    return (
        f"{provider}-"
        f"{anime_id}"
        f"{suffix}"
    )


def download_cover_image(
    anime,
):

    image_url = get_cover_image_url(
        anime
    )

    if not image_url:

        return None

    cache_directory = (
        get_cover_cache_directory()
    )

    filename = safe_cover_filename(
        anime,
        image_url,
    )

    image_path = (
        cache_directory
        / filename
    )

    if (
        image_path.exists()
        and image_path.stat().st_size > 0
    ):

        return image_path

    try:

        response = requests.get(
            image_url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Anime-Release-CLI/"
                    f"{get_cli_version()}"
                )
            },
        )

        response.raise_for_status()

        content_type = (
            response.headers.get(
                "Content-Type",
                ""
            )
        ).lower()

        if (
            content_type
            and not content_type.startswith(
                "image/"
            )
        ):

            return None

        image_path.write_bytes(
            response.content
        )

    except (
        requests.exceptions.RequestException,
        OSError,
    ):

        return None

    return image_path


def clean_description(
    description,
):

    if not description:

        return ""

    description = html.unescape(
        description
    )

    description = re.sub(
        r"<br\s*/?>",
        "\n",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"</p>",
        "\n",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"<[^>]+>",
        "",
        description,
    )

    description = re.sub(
        r"\n\s*\n+",
        "\n",
        description,
    )

    return description.strip()


# ============================================================
# NATIVE TERMINAL IMAGE SUPPORT
# ============================================================


def supports_native_inline_images():

    term_program = (
        os.environ.get(
            "TERM_PROGRAM",
            ""
        )
        .strip()
        .lower()
    )

    if "warp" in term_program:

        return True

    if "iterm" in term_program:

        return True

    if os.environ.get(
        "ITERM_SESSION_ID"
    ):

        return True

    return False


def build_native_image_sequence(
    image_path,
    width=24,
    rows=18,
):

    try:

        image_data = (
            image_path.read_bytes()
        )

    except OSError:

        return None

    if not image_data:

        return None

    encoded_image = (
        base64.b64encode(
            image_data
        ).decode(
            "ascii"
        )
    )

    encoded_name = (
        base64.b64encode(
            image_path.name.encode(
                "utf-8"
            )
        ).decode(
            "ascii"
        )
    )

    return (
        "\033]1337;File="
        f"name={encoded_name};"
        f"inline=1;"
        f"width={width};"
        f"height={rows};"
        f"preserveAspectRatio=1:"
        f"{encoded_image}"
        "\a"
    )


QUADRANT_GLYPHS = {
    0b0000: " ",
    0b0001: "▘",
    0b0010: "▝",
    0b0011: "▀",
    0b0100: "▖",
    0b0101: "▌",
    0b0110: "▞",
    0b0111: "▛",
    0b1000: "▗",
    0b1001: "▚",
    0b1010: "▐",
    0b1011: "▜",
    0b1100: "▄",
    0b1101: "▙",
    0b1110: "▟",
    0b1111: "█",
}


def average_rgb(
    colors,
):

    if not colors:

        return (
            0,
            0,
            0,
        )

    return tuple(
        int(
            sum(
                color[channel]
                for color in colors
            )
            / len(
                colors
            )
        )

        for channel in range(
            3
        )
    )


def color_distance(
    first,
    second,
):

    red_difference = (
        first[0]
        - second[0]
    )

    green_difference = (
        first[1]
        - second[1]
    )

    blue_difference = (
        first[2]
        - second[2]
    )

    return (
        red_difference
        * red_difference
        * 0.30

        + green_difference
        * green_difference
        * 0.59

        + blue_difference
        * blue_difference
        * 0.11
    )


def crop_cover_for_terminal(
    image,
    width,
    rows,
):

    source_width, source_height = (
        image.size
    )

    cell_aspect = 2.0

    visible_width = (
        width
    )

    visible_height = (
        rows
        * cell_aspect
    )

    target_ratio = (
        visible_width
        / visible_height
    )

    source_ratio = (
        source_width
        / source_height
    )

    if source_ratio > target_ratio:

        crop_width = int(
            source_height
            * target_ratio
        )

        left = (
            source_width
            - crop_width
        ) // 2

        image = image.crop(
            (
                left,
                0,
                left + crop_width,
                source_height,
            )
        )

    else:

        crop_height = int(
            source_width
            / target_ratio
        )

        top = (
            source_height
            - crop_height
        ) // 2

        image = image.crop(
            (
                0,
                top,
                source_width,
                top + crop_height,
            )
        )

    return image


def best_quadrant_cell(
    colors,
):

    best_error = None
    best_mask = 0

    best_foreground = (
        0,
        0,
        0,
    )

    best_background = (
        0,
        0,
        0,
    )

    for mask in range(
        16
    ):

        foreground_pixels = []

        background_pixels = []

        for index, color in enumerate(
            colors
        ):

            if (
                mask
                & (
                    1 << index
                )
            ):

                foreground_pixels.append(
                    color
                )

            else:

                background_pixels.append(
                    color
                )

        if foreground_pixels:

            foreground = average_rgb(
                foreground_pixels
            )

        elif background_pixels:

            foreground = average_rgb(
                background_pixels
            )

        else:

            foreground = (
                0,
                0,
                0,
            )

        if background_pixels:

            background = average_rgb(
                background_pixels
            )

        else:

            background = foreground

        error = 0

        for index, color in enumerate(
            colors
        ):

            if (
                mask
                & (
                    1 << index
                )
            ):

                candidate = foreground

            else:

                candidate = background

            error += color_distance(
                color,
                candidate,
            )

        if (
            best_error is None
            or error < best_error
        ):

            best_error = error

            best_mask = mask

            best_foreground = foreground

            best_background = background

    return (
        QUADRANT_GLYPHS[
            best_mask
        ],
        best_foreground,
        best_background,
    )


def render_cover_ansi(
    image_path,
    width=28,
    rows=22,
):

    try:

        with Image.open(
            image_path
        ) as image:

            image = image.convert(
                "RGB"
            )

            image = crop_cover_for_terminal(
                image,
                width,
                rows,
            )

            target_width = (
                width * 2
            )

            target_height = (
                rows * 2
            )

            supersample = 4

            high_width = (
                target_width
                * supersample
            )

            high_height = (
                target_height
                * supersample
            )

            image = image.resize(
                (
                    high_width,
                    high_height,
                ),
                Image.Resampling.LANCZOS,
            )

            image = image.filter(
                ImageFilter.UnsharpMask(
                    radius=1.25,
                    percent=130,
                    threshold=3,
                )
            )

            image = ImageEnhance.Contrast(
                image
            ).enhance(
                1.05
            )

            image = ImageEnhance.Color(
                image
            ).enhance(
                1.03
            )

            image = image.resize(
                (
                    target_width,
                    target_height,
                ),
                Image.Resampling.LANCZOS,
            )

            pixels = image.load()

            output_lines = []

            for y in range(
                0,
                target_height,
                2,
            ):

                line = ""

                for x in range(
                    0,
                    target_width,
                    2,
                ):

                    colors = [
                        pixels[
                            x,
                            y,
                        ],

                        pixels[
                            x + 1,
                            y,
                        ],

                        pixels[
                            x,
                            y + 1,
                        ],

                        pixels[
                            x + 1,
                            y + 1,
                        ],
                    ]

                    (
                        glyph,
                        foreground,
                        background,
                    ) = best_quadrant_cell(
                        colors
                    )

                    line += (
                        f"\033[38;2;"
                        f"{foreground[0]};"
                        f"{foreground[1]};"
                        f"{foreground[2]}m"
                        f"\033[48;2;"
                        f"{background[0]};"
                        f"{background[1]};"
                        f"{background[2]}m"
                        f"{glyph}"
                    )

                line += RESET

                output_lines.append(
                    line
                )

            return output_lines

    except (
        OSError,
        ValueError,
    ):

        return []


def color_metadata_line(
    label,
    value,
):

    return (
        f"{GREEN}"
        f"{label}:"
        f"{RESET}"
        f" "
        f"{WHITE}"
        f"{value}"
        f"{RESET}"
    )


def get_anime_card_text(
    anime,
    width,
    max_rows,
):

    lines = []

    title = anime_title(
        anime
    )

    title_lines = textwrap.wrap(
        title.upper(),
        width=max(
            20,
            width,
        ),
    )

    for title_line in title_lines:

        lines.append(
            f"{GREEN}"
            f"{title_line}"
            f"{RESET}"
        )

    lines.append(
        ""
    )

    lines.append(
        color_metadata_line(
            "Type",
            anime.get(
                "format"
            )
            or "TBA",
        )
    )

    lines.append(
        color_metadata_line(
            "Episodes",
            anime.get(
                "episodes"
            )
            or "TBA",
        )
    )

    lines.append(
        color_metadata_line(
            "Status",
            anime.get(
                "status"
            )
            or "TBA",
        )
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

    studio_names = ", ".join(
        studio.get(
            "name",
            ""
        )

        for studio in studios

        if studio.get(
            "name"
        )
    )

    if studio_names:

        lines.append(
            color_metadata_line(
                "Studio",
                studio_names,
            )
        )

    lines.append(
        color_metadata_line(
            "Source",
            anime.get(
                "source"
            )
            or "TBA",
        )
    )

    genres = (
        anime.get(
            "genres",
            [],
        )
    )

    if genres:

        genre_text = ", ".join(
            genres
        )

        genre_lines = textwrap.wrap(
            genre_text,
            width=max(
                15,
                width - 10,
            ),
        )

        if genre_lines:

            lines.append(
                color_metadata_line(
                    "Genres",
                    genre_lines[0],
                )
            )

            for continuation in (
                genre_lines[1:]
            ):

                lines.append(
                    f"{WHITE}"
                    f"{' ' * 8}"
                    f"{continuation}"
                    f"{RESET}"
                )

    start_date = format_date(
        anime.get(
            "startDate"
        )
    )

    end_date = format_date(
        anime.get(
            "endDate"
        )
    )

    if (
        start_date != "TBA"
        and end_date != "TBA"
    ):

        lines.append(
            color_metadata_line(
                "Aired",
                (
                    f"{start_date} — "
                    f"{end_date}"
                ),
            )
        )

    elif start_date != "TBA":

        lines.append(
            color_metadata_line(
                "Started",
                start_date,
            )
        )

    next_episode = anime.get(
        "nextAiringEpisode"
    )

    if next_episode:

        episode = next_episode.get(
            "episode"
        )

        airing_at = next_episode.get(
            "airingAt"
        )

        if episode:

            lines.append(
                color_metadata_line(
                    "Next Ep",
                    episode,
                )
            )

        if airing_at:

            local_time = (
                datetime.fromtimestamp(
                    airing_at
                ).astimezone()
            )

            lines.append(
                color_metadata_line(
                    "Airs",
                    local_time.strftime(
                        "%b %d, %Y "
                        "%I:%M %p %Z"
                    ),
                )
            )

    description = clean_description(
        anime.get(
            "description"
        )
    )

    if description:

        lines.append(
            ""
        )

        lines.append(
            f"{GREEN}"
            f"Synopsis:"
            f"{RESET}"
        )

        wrapped_description = (
            textwrap.wrap(
                description,
                width=max(
                    20,
                    width,
                ),
            )
        )

        available = (
            max_rows
            - len(
                lines
            )
        )

        if available > 0:

            for paragraph_line in (
                wrapped_description[
                    :available
                ]
            ):

                lines.append(
                    f"{WHITE}"
                    f"{paragraph_line}"
                    f"{RESET}"
                )

    return lines[
        :max_rows
    ]


def ansi_visible_length(
    text,
):

    ansi_escape = re.compile(
        r"\x1b\[[0-9;]*m"
    )

    clean = ansi_escape.sub(
        "",
        text,
    )

    return len(
        clean
    )


def ansi_pad(
    text,
    width,
):

    visible_length = (
        ansi_visible_length(
            text
        )
    )

    remaining = max(
        0,
        width - visible_length,
    )

    return (
        text
        + (
            " " * remaining
        )
    )


def render_native_anime_info_card(
    anime,
    image_path,
):

    if not supports_native_inline_images():

        return False

    terminal_width = (
        shutil.get_terminal_size(
            fallback=(
                120,
                30,
            )
        ).columns
    )

    if terminal_width < 90:

        return False

    image_width = 24
    image_rows = 18
    gap = 3

    card_width = min(
        terminal_width - 2,
        94,
    )

    inner_width = (
        card_width - 2
    )

    text_width = (
        inner_width
        - image_width
        - gap
        - 2
    )

    if text_width < 42:

        return False

    image_sequence = (
        build_native_image_sequence(
            image_path,
            width=image_width,
            rows=image_rows,
        )
    )

    if not image_sequence:

        return False

    text_lines = get_anime_card_text(
        anime,
        width=text_width,
        max_rows=image_rows,
    )

    while len(
        text_lines
    ) < image_rows:

        text_lines.append(
            ""
        )

    print()

    print(
        f"{GREEN}"
        f"┌"
        f"{'─' * inner_width}"
        f"┐"
        f"{RESET}"
    )

    for _ in range(
        image_rows
    ):

        print(
            f"{GREEN}"
            f"│"
            f"{RESET}"
            f"{' ' * inner_width}"
            f"{GREEN}"
            f"│"
            f"{RESET}"
        )

    print(
        f"{GREEN}"
        f"└"
        f"{'─' * inner_width}"
        f"┘"
        f"{RESET}"
    )

    print(
        f"{DIM}"
        f"Anime Release CLI"
        f" | Data: "
        f"{provider_name(anime)}"
        f" | v{get_cli_version()}"
        f"{RESET}"
    )

    rows_up = (
        image_rows + 2
    )

    sys.stdout.write(
        f"\033[{rows_up}A"
    )

    sys.stdout.write(
        "\r"
    )

    sys.stdout.write(
        "\033[2C"
    )

    sys.stdout.write(
        "\0337"
    )

    sys.stdout.write(
        image_sequence
    )

    sys.stdout.write(
        "\0338"
    )

    text_column = (
        2
        + image_width
        + gap
    )

    for index, line in enumerate(
        text_lines
    ):

        if index > 0:

            sys.stdout.write(
                "\033[1B"
            )

        sys.stdout.write(
            "\r"
        )

        sys.stdout.write(
            f"\033[{text_column}C"
        )

        sys.stdout.write(
            line
        )

    remaining_rows = (
        image_rows
        - len(
            text_lines
        )
    )

    if remaining_rows > 0:

        sys.stdout.write(
            f"\033[{remaining_rows}B"
        )

    sys.stdout.write(
        "\033[3B"
    )

    sys.stdout.write(
        "\r"
    )

    sys.stdout.flush()

    return True


def render_ansi_anime_info_card(
    anime,
    image_path,
):

    terminal_width = (
        shutil.get_terminal_size(
            fallback=(
                120,
                30,
            )
        ).columns
    )

    if terminal_width < 80:

        return False

    image_width = 28
    image_rows = 22
    gap = 4

    card_width = min(
        terminal_width - 2,
        112,
    )

    inner_width = (
        card_width - 2
    )

    text_width = (
        inner_width
        - image_width
        - gap
        - 2
    )

    if text_width < 35:

        return False

    image_lines = render_cover_ansi(
        image_path,
        width=image_width,
        rows=image_rows,
    )

    if not image_lines:

        return False

    text_lines = get_anime_card_text(
        anime,
        width=text_width,
        max_rows=image_rows,
    )

    while len(
        text_lines
    ) < image_rows:

        text_lines.append(
            ""
        )

    print()

    print(
        f"{GREEN}"
        f"┌"
        f"{'─' * inner_width}"
        f"┐"
        f"{RESET}"
    )

    for row in range(
        image_rows
    ):

        image_line = (
            image_lines[
                row
            ]
        )

        text_line = (
            text_lines[
                row
            ]
        )

        padded_text = ansi_pad(
            text_line,
            text_width,
        )

        print(
            f"{GREEN}"
            f"│"
            f"{RESET}"
            f" "
            f"{image_line}"
            f"{' ' * gap}"
            f"{padded_text}"
            f" "
            f"{GREEN}"
            f"│"
            f"{RESET}"
        )

    print(
        f"{GREEN}"
        f"└"
        f"{'─' * inner_width}"
        f"┘"
        f"{RESET}"
    )

    print(
        f"{DIM}"
        f"Data source: "
        f"{provider_name(anime)}"
        f"{RESET}"
    )

    return True


def render_anime_info_card(
    anime,
):

    image_path = download_cover_image(
        anime
    )

    if not image_path:

        return False

    native_rendered = (
        render_native_anime_info_card(
            anime,
            image_path,
        )
    )

    if native_rendered:

        return True

    return render_ansi_anime_info_card(
        anime,
        image_path,
    )


def get_update_banner_path():

    cache_directory = (
        get_cover_cache_directory()
        .parent
    )

    banner_path = (
        cache_directory
        / "update-banner.png"
    )

    if banner_path.exists():

        return banner_path

    image = Image.new(
        "RGB",
        (
            900,
            420,
        ),
        (
            12,
            16,
            14,
        ),
    )

    draw = ImageDraw.Draw(
        image
    )

    draw.rectangle(
        (
            20,
            20,
            880,
            400,
        ),
        outline=(
            102,
            255,
            0,
        ),
        width=6,
    )

    draw.text(
        (
            70,
            120,
        ),
        "ANIME RELEASE CLI",
        fill=(
            102,
            255,
            0,
        ),
    )

    draw.text(
        (
            70,
            190,
        ),
        "UPDATE",
        fill=(
            235,
            235,
            235,
        ),
    )

    draw.text(
        (
            70,
            260,
        ),
        f"v{get_cli_version()}",
        fill=(
            135,
            135,
            135,
        ),
    )

    image.save(
        banner_path
    )

    return banner_path


def render_update_visual():

    try:

        image_path = (
            get_update_banner_path()
        )

    except OSError:

        return False

    if supports_native_inline_images():

        image_sequence = (
            build_native_image_sequence(
                image_path,
                width=42,
                rows=12,
            )
        )

        if image_sequence:

            print()

            sys.stdout.write(
                image_sequence
            )

            sys.stdout.write(
                "\n"
            )

            sys.stdout.flush()

            return True

    image_lines = render_cover_ansi(
        image_path,
        width=42,
        rows=12,
    )

    if not image_lines:

        return False

    print()

    for line in image_lines:

        print(
            line
        )

    return True


# ============================================================
# STANDARD CLI
# ============================================================


def display_anime_detail(
    anime,
    show_description=True,
):

    rendered = render_anime_info_card(
        anime
    )

    if rendered:

        return True

    print()

    print(
        format_anime_details(
            anime
        )
    )

    if show_description:

        description = clean_description(
            anime.get(
                "description"
            )
        )

        if description:

            print()

            print(
                "Description:"
            )

            print(
                description
            )

    print()

    print(
        f"Data source: "
        f"{provider_name(anime)}"
    )

    return False


def print_anime_entry(
    anime,
    index=None,
):

    print()

    prefix = ""

    if index is not None:

        prefix = (
            f"{index}. "
        )

    print(
        f"{prefix}"
        f"{anime_title(anime)}"
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

        print_anime_entry(
            anime,
            index=index,
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


def find_full_anime_details(
    title,
):

    entries = get_anime_entries(
        title
    )

    if not entries:

        return None

    normalized_title = (
        title.strip().lower()
    )

    for anime in entries:

        titles = anime.get(
            "title",
            {},
        )

        candidates = [
            titles.get(
                "english"
            ),
            titles.get(
                "romaji"
            ),
            titles.get(
                "native"
            ),
        ]

        for candidate in candidates:

            if (
                candidate
                and candidate.strip().lower()
                == normalized_title
            ):

                return anime

    return entries[0]


def display_anime_by_title(
    title,
):

    anime = find_full_anime_details(
        title
    )

    if not anime:

        print()

        print(
            "Unable to load anime artwork."
        )

        return False

    return display_anime_detail(
        anime
    )


def choose_from_anime_list(
    anime_list,
):

    if not anime_list:

        return None

    print()

    while True:

        choice = input(
            "Choose an entry for details "
            "(or press Enter to finish): "
        ).strip()

        if not choice:

            return None

        try:

            choice = int(
                choice
            )

        except ValueError:

            print(
                "Invalid selection."
            )

            continue

        if (
            1
            <= choice
            <= len(anime_list)
        ):

            return anime_list[
                choice - 1
            ]

        print(
            "Invalid selection."
        )


def handle_search(title):

    anime = choose_anime(
        title
    )

    if not anime:

        return

    display_anime_detail(
        anime
    )


def handle_info(title):

    anime = choose_anime(
        title
    )

    if not anime:

        return

    display_anime_detail(
        anime
    )


def handle_schedule(title):

    anime = choose_anime(
        title
    )

    if not anime:

        return

    display_anime_detail(
        anime
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

    airing_at = next_episode.get(
        "airingAt"
    )

    if not airing_at:

        print(
            "Episode date is currently TBA."
        )

        return

    date = datetime.fromtimestamp(
        airing_at
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

    display_anime_detail(
        anime
    )

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
    selectable_nodes = []

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
    display_index = 1

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
                f"  {display_index}. "
                f"{title_text}"
            )

            print(
                f"     "
                f"{' | '.join(details)}"
            )

            selectable_nodes.append(
                node
            )

            display_index += 1

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
                f"  {display_index}. "
                f"{anime_title(node)}"
            )

            selectable_nodes.append(
                node
            )

            display_index += 1

    selected = choose_from_anime_list(
        selectable_nodes
    )

    if not selected:

        return

    display_anime_by_title(
        anime_title(
            selected
        )
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

    print()

    print(
        studio.upper()
    )

    print(
        "─" * 60
    )

    for index, anime in enumerate(
        anime_list,
        start=1,
    ):

        print_anime_entry(
            anime,
            index=index,
        )

    selected = choose_from_anime_list(
        anime_list
    )

    if not selected:

        return

    display_anime_by_title(
        anime_title(
            selected
        )
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

    for index, anime in enumerate(
        anime_list,
        start=1,
    ):

        print_anime_entry(
            anime,
            index=index,
        )

    print()

    print(
        f"Data source: "
        f"{provider_name(anime_list[0])}"
    )

    selected = choose_from_anime_list(
        anime_list
    )

    if not selected:

        return

    if get_cover_image_url(
        selected
    ):

        display_anime_detail(
            selected
        )

    else:

        display_anime_by_title(
            anime_title(
                selected
            )
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

    for index, anime in enumerate(
        anime_list,
        start=1,
    ):

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
            f"{index}. "
            f"{title}"
        )

        print(
            f"   Start:    {start}"
        )

        if anime.get(
            "format"
        ):

            print(
                f"   Format:   "
                f"{anime['format']}"
            )

    print()

    print(
        f"Data source: "
        f"{provider_name(anime_list[0])}"
    )

    selected = choose_from_anime_list(
        anime_list
    )

    if not selected:

        return

    display_anime_by_title(
        anime_title(
            selected
        )
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

    for index, item in enumerate(
        schedules,
        start=1,
    ):

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

        if provider in (
            "tsuzuki",
            "animeschedule",
        ):

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
                f"{index}. "
                f"{time.strftime('%I:%M %p')} "
                f"{episode_text} "
                f"{title}"
                f"{detail_text}"
            )

        else:

            print(
                f"{index}. "
                f"{time.strftime('%I:%M %p')} "
                f"{episode_text} "
                f"{title}"
            )

    print()

    print(
        f"Data source: "
        f"{provider_name(schedules[0])}"
    )

    print()

    while True:

        choice = input(
            "Choose an entry for details "
            "(or press Enter to finish): "
        ).strip()

        if not choice:

            return

        try:

            choice = int(
                choice
            )

        except ValueError:

            print(
                "Invalid selection."
            )

            continue

        if (
            1
            <= choice
            <= len(schedules)
        ):

            selected = schedules[
                choice - 1
            ]

            selected_title = anime_title(
                selected[
                    "media"
                ]
            )

            display_anime_by_title(
                selected_title
            )

            return

        print(
            "Invalid selection."
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

    try:

        anime = choose_tsuzuki_airing(
            title
        )

    except TsuzukiAPIError as error:

        print()

        print(
            f"Tsuzuki unavailable: "
            f"{error}"
        )

        print(
            "Using anime metadata "
            "fallback."
        )

        anime = choose_anime(
            title
        )

        if not anime:

            return

        display_anime_detail(
            anime
        )

        return

    if not anime:

        return

    title_text = tsuzuki_title(
        anime
    )

    display_anime_by_title(
        title_text
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
            "Metadata source: AniList/Kitsu"
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

                platform = (
                    "Amazon Prime Video"
                )

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
        "Metadata source: AniList/Kitsu"
    )


UPDATE_REPOSITORY = (
    "git+https://github.com/"
    "LeftfaceKing/"
    "anime-release-cli.git"
)


def handle_update():

    render_update_visual()

    pipx_path = shutil.which(
        "pipx"
    )

    if not pipx_path:

        print()

        print(
            "Unable to update Anime Release CLI."
        )

        print(
            "pipx is not installed or "
            "could not be found."
        )

        print()

        print(
            "Install pipx, then run:"
        )

        print(
            "ani update"
        )

        return

    print()

    print(
        "ANIME RELEASE CLI UPDATER"
    )

    print(
        "─" * 60
    )

    print(
        f"Current version: "
        f"{get_cli_version()}"
    )

    print()

    print(
        "Checking GitHub for the "
        "latest version..."
    )

    print()

    try:

        result = subprocess.run(
            [
                pipx_path,
                "install",
                "--force",
                UPDATE_REPOSITORY,
            ],
            check=False,
        )

    except OSError as error:

        print()

        print(
            f"Update failed: {error}"
        )

        return

    if result.returncode != 0:

        print()

        print(
            "Anime Release CLI "
            "could not be updated."
        )

        return

    print()

    print(
        "Update complete."
    )

    print()

    print(
        "Run:"
    )

    print(
        "ani --version"
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

    sub.add_parser(
        "update"
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

        elif args.command == "update":

            handle_update()

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
