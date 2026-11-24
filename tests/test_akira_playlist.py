import os
import re
import unittest

from utils.local_source_importer import parse_local_source_file


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLAYLIST = os.path.join(ROOT, "tests", "fixtures", "akira-iptv.m3u")
SUBSCRIBE = os.path.join(ROOT, "config", "subscribe.txt")
CONFIG = os.path.join(ROOT, "config", "config.ini")
ALIAS = os.path.join(ROOT, "config", "alias.txt")
TEMPLATE = os.path.join(ROOT, "config", "demo.txt")
SOURCE_URL = "https://raw.githubusercontent.com/akiralereal/iptv/main/IPTV.m3u"


def _alias_map():
    mapping = {}
    patterns = []
    with open(ALIAS, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#") or "," not in line:
                continue
            parts = [part.strip() for part in line.split(",")]
            primary = parts[0]
            for alias in parts:
                mapping[alias] = primary
                if alias.startswith("re:"):
                    try:
                        patterns.append((re.compile(alias[3:]), primary))
                    except re.error:
                        continue
    return mapping, patterns


def _primary_name(name, mapping, patterns):
    if name in mapping:
        return mapping[name]
    for pattern, primary in patterns:
        if pattern.search(name):
            return primary
    return name


def _template_names():
    names = set()
    with open(TEMPLATE, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "#genre#" in line:
                continue
            names.add(line.split(",")[0].split("，")[0].strip())
    return names


class AkiraPlaylistTests(unittest.TestCase):
    def test_source_playlist_has_twenty_playable_channels(self):
        records, errors = parse_local_source_file(PLAYLIST)
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 20)
        self.assertEqual(len({item.channel for item in records}), 20)
        self.assertEqual(len({item.url for item in records}), 20)

    def test_subscription_keeps_every_source_channel(self):
        with open(SUBSCRIBE, encoding="utf-8") as handle:
            subscribe = handle.read()
        whitelist = subscribe.split("[WHITELIST]", 1)[1]
        self.assertIn(SOURCE_URL, whitelist)
        self.assertNotIn(f"# {SOURCE_URL}", subscribe)
        self.assertNotIn(f"#{SOURCE_URL}", subscribe)

        with open(CONFIG, encoding="utf-8") as handle:
            config = handle.read()
        self.assertRegex(config, r"(?m)^open_unmatch_category = True$")

        records, _ = parse_local_source_file(PLAYLIST)
        mapping, patterns = _alias_map()
        template = _template_names()
        served = [_primary_name(item.channel, mapping, patterns) for item in records]
        self.assertEqual(len(set(served)), len(records))
        self.assertTrue(set(served) & template)
        self.assertTrue(set(served) - template)


if __name__ == "__main__":
    unittest.main()
