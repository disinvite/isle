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
    """Generate a function that will display the diff according to
    the reccmp display preferences."""

    def formatter(orig_addr, saved, new) -> str:
        # Effective match not considered here

        old_pct = "new"
        new_pct = "gone"
        name = ""
        recomp_addr = "n/a"

        if new is not None:
            new_pct = (
                "stub"
                if new.get("stub", False)
                else percent_string(new["matching"], False, is_plain)
            )

            # Prefer the current name of this function if we have it.
            # We are using the original address as the key.
            # A function being renamed is not of interest here.
            name = new.get("name", "")
            recomp_addr = new.get("recomp", "n/a")

        if saved is not None:
            old_pct = (
                "stub"
                if saved.get("stub", False)
                else percent_string(saved["matching"], False, is_plain)
            )

            if name == "":
                name = saved.get("name", "")

        if show_both_addrs:
            addr_string = f"{orig_addr} / {recomp_addr:10}"
        else:
            addr_string = orig_addr

        # The ANSI codes from colorama counted towards string length,
        # so displaying this as an ascii-like spreadsheet
        # (using f-string formatting) would take some effort.
        return f"{addr_string} - {name} ({old_pct} -> {new_pct})"

    return formatter


def diff_json(
    saved_data, new_data, show_both_addrs: bool = False, is_plain: bool = False
):
    """Using a saved copy of the diff summary and the current data, print a
    report showing which functions/symbols have changed match percentage."""

    # Convert to dict, using orig_addr as key
    saved_invert = {obj["address"]: obj for obj in saved_data}
    new_invert = {obj["address"]: obj for obj in new_data}

    all_addrs = set(saved_invert.keys()).union(new_invert.keys())

    # Put all the information in one place so we can decide how each item changed.
    combined = {
        addr: (
            saved_invert.get(addr),
            new_invert.get(addr),
        )
        for addr in sorted(all_addrs)
    }

    # The criteria for diff judgement is in these dict comprehensions:
    new_functions = {
        key: (saved, new) for key, (saved, new) in combined.items() if saved is None
    }

    dropped_functions = {
        key: (saved, new) for key, (saved, new) in combined.items() if new is None
    }

    # TODO: move these two into functions if the assessment gets more complex
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
