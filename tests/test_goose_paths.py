from pathlib import Path
import pytest

from metacoder.coders.goose import get_home_env_var, get_goose_config_path


def _norm(p: Path | str) -> str:
    """Normalize path separators & strip trailing slashes for stable compares."""
    s = str(p).replace("\\", "/")
    return s[:-1] if s.endswith("/") else s


@pytest.mark.parametrize(
    "platform_name, xdg_value, expected_env",
    [
        ("Windows", None, "APPDATA"),
        ("Linux", None, "HOME"),
        ("Darwin", None, "HOME"),
        ("Linux", "/custom/xdg", "XDG_CONFIG_HOME"),
        ("Darwin", "/Users/alice/.conf", "XDG_CONFIG_HOME"),
    ],
)
def test_env_var_selection(monkeypatch, platform_name, xdg_value, expected_env):
    # Simulate platform
    import platform as _platform

    monkeypatch.setattr(_platform, "system", lambda: platform_name)

    # Simulate XDG presence/absence
    if xdg_value is not None:
        monkeypatch.setenv("XDG_CONFIG_HOME", xdg_value)
    else:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    actual = get_home_env_var()
    assert actual == expected_env


@pytest.mark.parametrize(
    "platform_name, xdg_value, expected_env, expected_rel_dir",
    [
        ("Windows", None, "APPDATA", "Block/goose/config"),
        ("Linux", None, "HOME", ".config/goose"),
        ("Darwin", None, "HOME", ".config/goose"),
        ("Linux", "/custom/xdg", "XDG_CONFIG_HOME", "goose"),
        ("Darwin", "/Users/alice/.conf", "XDG_CONFIG_HOME", "goose"),
    ],
)
def test_config_path_matches_env(
    monkeypatch, platform_name, xdg_value, expected_env, expected_rel_dir
):
    import platform as _platform

    monkeypatch.setattr(_platform, "system", lambda: platform_name)

    if xdg_value is not None:
        monkeypatch.setenv("XDG_CONFIG_HOME", xdg_value)
    else:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    env_var = get_home_env_var()
    rel_path = get_goose_config_path()

    assert env_var == expected_env
    assert _norm(rel_path) == expected_rel_dir


@pytest.mark.parametrize(
    "platform_name, xdg_value, workdir, expected_effective_dir",
    [
        ("Windows", None, "C:/tmp/work", "C:/tmp/work/Block/goose/config/config.yaml"),
        ("Linux", None, "/tmp/work", "/tmp/work/.config/goose/config.yaml"),
        (
            "Darwin",
            None,
            "/Users/alice/work",
            "/Users/alice/work/.config/goose/config.yaml",
        ),
        ("Linux", "/custom/xdg", "/tmp/work", "/tmp/work/goose/config.yaml"),
        (
            "Darwin",
            "/Users/alice/.conf",
            "/Users/alice/work",
            "/Users/alice/work/goose/config.yaml",
        ),
    ],
)
def test_effective_config_location(
    monkeypatch, platform_name, xdg_value, workdir, expected_effective_dir
):
    import platform as _platform

    monkeypatch.setattr(_platform, "system", lambda: platform_name)

    if xdg_value is not None:
        monkeypatch.setenv("XDG_CONFIG_HOME", xdg_value)
    else:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    local_home_path = Path(workdir)

    goose_config_dir = local_home_path / get_goose_config_path()
    goose_cfg_file = goose_config_dir / "config.yaml"

    assert _norm(goose_cfg_file) == _norm(expected_effective_dir)
