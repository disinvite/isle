import os
import sys
import colorama


def print_diff(udiff, plain):
    if udiff is None:
        return False

    has_diff = False
    for line in udiff:
        has_diff = True
        color = ""
        if line.startswith("++") or line.startswith("@@") or line.startswith("--"):
            # Skip unneeded parts of the diff for the brief view
            continue
        # Work out color if we are printing color
        if not plain:
            if line.startswith("+"):
                color = colorama.Fore.GREEN
            elif line.startswith("-"):
                color = colorama.Fore.RED
        print(color + line)
        # Reset color if we're printing in color
        if not plain:
            print(colorama.Style.RESET_ALL, end="")
    return has_diff


def get_percent_color(value: float) -> str:
    """Return colorama ANSI escape character for the given decimal value."""
    if value == 1.0:
        return colorama.Fore.GREEN
    if value > 0.8:
        return colorama.Fore.YELLOW

    return colorama.Fore.RED


def percent_string(
    ratio: float, is_effective: bool = False, is_plain: bool = False
) -> str:
    """Helper to construct a percentage string from the given ratio.
    If is_effective (i.e. effective match), indicate that with the asterisk.
    If is_plain, don't use colorama ANSI codes."""

    percenttext = f"{(ratio * 100):.2f}%"
    effective_star = "*" if is_effective else ""

    if is_plain:
        return percenttext + effective_star

    return "".join(
        [
            get_percent_color(ratio),
            percenttext,
            colorama.Fore.RED if is_effective else "",
            effective_star,
            colorama.Style.RESET_ALL,
        ]
    )


def diff_json_display(show_both_addrs: bool = False, is_plain: bool = False):
    # pylint: disable=unused-argument
    # TODO
    """Generate and return print function"""

    def formatter(orig_addr, saved, new) -> str:
        # Effective match not considered here

        old_pct = (
            ""
            if saved is None
            else (
                "stub"
                if saved.get("stub", False)
                else percent_string(saved["matching"], False, is_plain)
            )
        )
        new_pct = (
            ""
            if new is None
            else (
                "stub"
                if new.get("stub", False)
                else percent_string(new["matching"], False, is_plain)
            )
        )

        name = (
            new.get("name")
            if new is not None
            else (saved.get("name") if saved is not None else "???")
        )

        if show_both_addrs:
            addr_string = (
                f"{orig_addr} / {new['recomp'] if new is not None else 'n/a':10}"
            )
        else:
            addr_string = orig_addr

        return " ".join(
            [
                addr_string,
                f"{name:60}",
                f"{old_pct:10}",
                "->",
                f"{new_pct:10}",
            ]
        )

    return formatter


def diff_json(
    saved_data, new_data, show_both_addrs: bool = False, is_plain: bool = False
):
    # TODO: is_plain option
    # TODO: both_addrs option

    saved_invert = {
        obj["address"]: {
            "name": obj["name"],
            "matching": obj["matching"],
            "stub": obj.get("stub", False),
        }
        for obj in saved_data["data"]
    }

    new_invert = {
        obj["address"]: {
            "name": obj["name"],
            "matching": obj["matching"],
            "stub": obj.get("stub", False),
        }
        for obj in new_data
    }

    all_addrs = set(key for key, _ in saved_invert.items()).union(
        set(key for key, _ in new_invert.items())
    )

    combined = {
        addr: (
            saved_invert.get(addr),
            new_invert.get(addr),
        )
        for addr in all_addrs
    }

    new_functions = {
        key: (saved, new) for key, (saved, new) in combined.items() if saved is None
    }

    dropped_functions = {
        key: (saved, new) for key, (saved, new) in combined.items() if new is None
    }

    improved_functions = {
        key: (saved, new)
        for key, (saved, new) in combined.items()
        if saved is not None
        and new is not None
        and (
            new["matching"] > saved["matching"]
            or (not new.get("stub", False) and saved.get("stub", False))
        )
    }

    degraded_functions = {
        key: (saved, new)
        for key, (saved, new) in combined.items()
        if saved is not None
        and new is not None
        and (
            new["matching"] < saved["matching"]
            or (new.get("stub", False) and not saved.get("stub", False))
        )
    }

    get_diff_str = diff_json_display(show_both_addrs, is_plain)

    # TODO: sort by addr.
    for diff_name, diff_dict in [
        ("NEW", new_functions),
        ("IMPROVED", improved_functions),
        ("DEGRADED", degraded_functions),
        ("DROPPED", dropped_functions),
    ]:
        if len(diff_dict) == 0:
            continue

        print(f"{diff_name} ({len(diff_dict)}):")

        for addr, (saved, new) in diff_dict.items():
            print(get_diff_str(addr, saved, new))

        print()


def get_file_in_script_dir(fn):
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), fn)
