import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Optional

import httpx

HOME_PATH = os.path.dirname(os.path.dirname(__file__))


@dataclass
class BaseInstance:
    relative_filepath_without_ext: str
    
    def get_filepath(self, extension=".json"):
        return os.path.join(HOME_PATH, self.relative_filepath_without_ext + extension)
    
    def file_exists(self, extension=".json"):
        return os.path.exists(self.get_filepath())

    def makedirs(self):
        dirname = os.path.dirname(self.get_filepath())
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    
    def save_as_json(self, obj):
        with open(self.get_filepath(".json"), mode="w+", encoding="utf-8") as f:
            json.dump(obj, f, indent=4)
    
    def load_from_json(self):
        with open(self.get_filepath(".json"), mode="r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_list_as_txt(self, obj):
        to_save = "\n".join(obj)
        with open(self.get_filepath(".txt"), mode="w+", encoding="utf-8") as f:
            f.write(to_save)


class BaseDomainsGettter:
    def check_if_update(self, domains):
        if not self.inst.file_exists():
            return True
        domains_old = self.inst.load_from_json()
        return not (domains == domains_old)
    
    def update(self):
        self.inst.makedirs()
        domains = self.get_all_domains()
        if self.check_if_update(domains):
            self.inst.save_as_json(domains)
            self.inst.save_list_as_txt(domains)
            return True
        return False


@dataclass
class RegexFromUrlInstance(BaseInstance):
    url: str
    regex_pattern: str  # must be <domain>
    regex_group: str = "domain"
    
    def from_instance(self):
        return RegexFromUrl(self)


class RegexFromUrl(BaseDomainsGettter):
    def __init__(self, instance: RegexFromUrlInstance) -> None:
        self.inst = instance
        self.pattern = re.compile(self.inst.regex_pattern, flags=re.MULTILINE)
        super().__init__()
    
    def _get_match_and_other_text(self, text, index_from=0):
        match = self.pattern.search(text[index_from:])
        if match is None:
            return False
        return match, index_from+match.end()+1

    def get_all_domains_from_text(self, text):
        domain_list = list()
        index_from = 0
        for _ in range(len(self.pattern.findall(text))):
            res = self._get_match_and_other_text(text, index_from)
            if not res:
                break
            match, index_from = res
            if (match_group := match.groupdict().get(self.inst.regex_group)) is not None:
                domain_list.append(match_group)
        return sorted(domain_list)
    
    def get_all_domains(self):
        text = httpx.get(self.inst.url).text
        domain_list = self.get_all_domains_from_text(text)
        return domain_list


@dataclass
class RegexCroppedFromUrlInstance(RegexFromUrlInstance):
    crop_from: Optional[str] = None
    crop_to: Optional[str] = None
    
    def get_cropped(self, text):
        crop_from_i = text.index(self.crop_from)+len(self.crop_from) if self.crop_from is not None else 0
        crop_to_i = text.index(self.crop_to) if self.crop_to is not None else len(text)
        return text[crop_from_i:crop_to_i]
    
    def from_instance(self):
        return RegexCroppedFromUrl(self)


class RegexCroppedFromUrl(RegexFromUrl):
    def __init__(self, instance: RegexCroppedFromUrlInstance) -> None:
        super().__init__(instance)
    
    def get_all_domains_from_text(self, text):
        text = self.inst.get_cropped(text)
        return super().get_all_domains_from_text(text)


@dataclass
class JustFromUrlInstance(BaseInstance):
    url: str
    
    def from_instance(self):
        return JustFromUrl(self)


class JustFromUrl(BaseDomainsGettter):
    def __init__(self, instance: JustFromUrlInstance) -> None:
        self.inst = instance
        super().__init__()
    
    def get_all_domains(self):
        raw = httpx.get(self.inst.url).text
        domain_list = raw.strip("\n").split("\n")
        domain_list.sort()
        return domain_list


@dataclass
class JSONUsingCallableInstance(BaseInstance):
    url: str
    json_handle: Callable
    
    def from_instance(self):
        return JSONUsingCallable(self)


class JSONUsingCallable(BaseDomainsGettter):
    def __init__(self, instance: JSONUsingCallableInstance) -> None:
        self.inst = instance
        super().__init__()
    
    def get_all_domains(self):
        resp = httpx.get(self.inst.url)
        raw = resp.json()
        result = self.inst.json_handle(raw)
        return result


INSTANCES = [
    # ProxiTok
    RegexFromUrlInstance(relative_filepath_without_ext="instances/tiktok/proxitok/instances", url="https://raw.githubusercontent.com/wiki/pablouser1/ProxiTok/Public-instances.md", regex_pattern=r"\|\s+\[(?P<domain>[\w\-\.]+)\]\((?P<url>https?:\/\/(?:\w|\.|\/)+)\)\s+(?:\(Official\)\s+)?\|\s+(?P<cloudflare>Yes|No)\s+\|\s+(?P<flagemoji>\S+)\s+\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/tiktok/proxitok/onion", url="https://raw.githubusercontent.com/wiki/pablouser1/ProxiTok/Public-instances.md", regex_pattern=r"\|\s+\[(?P<domain>[\w\-\.]+\.onion)\]\((?P<url>https?:\/\/(?:\w|\.|\/)+)\)\s+\|"),
    # SimplyTranslate
    JustFromUrlInstance(relative_filepath_without_ext="instances/translate/simplytranslate/instances", url="https://simple-web.org/instances/simplytranslate"),
    JustFromUrlInstance(relative_filepath_without_ext="instances/translate/simplytranslate/onion", url="https://simple-web.org/instances/simplytranslate_onion"),
    JustFromUrlInstance(relative_filepath_without_ext="instances/translate/simplytranslate/i2p", url="https://simple-web.org/instances/simplytranslate_i2p"),
    JustFromUrlInstance(relative_filepath_without_ext="instances/translate/simplytranslate/loki", url="https://simple-web.org/instances/simplytranslate_loki"),
    # Whoogle
    RegexFromUrlInstance(relative_filepath_without_ext="instances/search/whoogle/instances", url="https://raw.githubusercontent.com/benbusby/whoogle-search/main/README.md", regex_pattern=r"\|\s+\[https?:\/\/(?P<domain>[\w\-\.]+)\]\((?P<url>https?:\/\/(?:\w|\.|\/)+)\/?\)\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<language>\S+)\s+\|\s?(?P<cloudflare>(?:✅\s|\s))\|$"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/search/whoogle/onion", url="https://raw.githubusercontent.com/benbusby/whoogle-search/main/README.md", regex_pattern=r"\|?\s+\[https?:\/\/(?P<domain>[\w\-\.]+\.onion)\]\((?P<url>https?:\/\/(?:\w|\.|\/)+)\/?\)\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<language>\S+)\s+\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/search/whoogle/i2p", url="https://raw.githubusercontent.com/benbusby/whoogle-search/main/README.md", regex_pattern=r"\|?\s+\[https?:\/\/(?P<domain>[\w\-\.]+\.i2p)\]\((?P<url>https?:\/\/(?:\w|\.|\/)+)\/?\)\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<language>\S+)\s+\|"),
    # LibreX
    RegexFromUrlInstance(relative_filepath_without_ext="instances/search/librex/instances", url="https://raw.githubusercontent.com/hnhx/librex/main/README.md", regex_group="clearnet", regex_pattern=r"\|\s+\[(?P<clearnet>[\w\-\.]+)\]\((?P<clearurl>https?:\/\/(?:\w|\.|\/)+)\)\s+\|\s+(?:❌|(?:\[✅\]\((?P<onion>http:(?:\w|\.|\/)+)\)))\s+\|\s+(?:❌|(?:\[✅\]\((?P<i2p>http:(?:\w|\.|\/)+)\)))\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+(?:\(OFFICIAL\s+INSTANCE\)\s+)?\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/search/librex/onion", url="https://raw.githubusercontent.com/hnhx/librex/main/README.md", regex_group="onion", regex_pattern=r"\|\s+\[(?P<clearnet>[\w\-\.]+)\]\((?P<clearurl>https?:\/\/(?:\w|\.|\/)+)\)\s+\|\s+(?:❌|(?:\[✅\]\((?P<onion>http:(?:\w|\.|\/)+)\)))\s+\|\s+(?:❌|(?:\[✅\]\((?P<i2p>http:(?:\w|\.|\/)+)\)))\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+(?:\(OFFICIAL\s+INSTANCE\)\s+)?\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/search/librex/i2p", url="https://raw.githubusercontent.com/hnhx/librex/main/README.md", regex_group="i2p", regex_pattern=r"\|\s+\[(?P<clearnet>[\w\-\.]+)\]\((?P<clearurl>https?:\/\/(?:\w|\.|\/)+)\)\s+\|\s+(?:❌|(?:\[✅\]\((?P<onion>http:(?:\w|\.|\/)+)\)))\s+\|\s+(?:❌|(?:\[✅\]\((?P<i2p>http:(?:\w|\.|\/)+)\)))\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+(?:\(OFFICIAL\s+INSTANCE\)\s+)?\|"),
    # Rimgo
    RegexFromUrlInstance(relative_filepath_without_ext="instances/imgur/rimgo/instances", url="https://codeberg.org/video-prize-ranch/rimgo/raw/branch/main/README.md", regex_pattern=r"\|\s+\[(?P<domain>[\w\-\.]+)\]\((?P<url>https?:\/\/[\w\-\.\/]+)\)+(?:\s+\(official\))?\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<provider>(?:[^\|])+)\s*\|\s+(?P<data>(?:[^\|])+)\s+\|(?P<notes>(?:[^\|])+)\|"),
    RegexCroppedFromUrlInstance(relative_filepath_without_ext="instances/imgur/rimgo/onion", url="https://codeberg.org/video-prize-ranch/rimgo/raw/branch/main/README.md", crop_from="### Tor", regex_pattern=r"\|\s+\[(?P<domain>[\w\-\.]+)\]\((?P<url>https?:\/\/[\w\-\.\/]+)\)+(?:\s+\(official\))?\s+\|\s+(?P<data>(?:[^\|])+)\s+\|(?P<notes>(?:[^\|])+)\|"),
    # Teddit
    RegexFromUrlInstance(relative_filepath_without_ext="instances/reddit/teddit/instances", url="https://codeberg.org/teddit/teddit/raw/branch/main/README.md", regex_pattern=r"\|\s+(?:\[(?P<domain>[\w\-\.]+)\]\((?P<url>https?:\/\/[\w\-\.\/]+)\)\s+)?\|\s+(?:\[(?:http:\/\/)?[\w\-\.\/\d]+\]\(http:\/\/(?P<onion>[\w\-\.\/\d]+\.onion\/?)\)\s+)?\|\s+(?:\[(?:http:\/\/)?[\w\-\.\/\d]+\]\(http:\/\/(?P<i2p>[\w\-\.\/\d]+\.i2p)\)\s+)?\|\s+(?P<notes>(?:[^\|])+)?\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/reddit/teddit/onion", url="https://codeberg.org/teddit/teddit/raw/branch/main/README.md", regex_group="onion", regex_pattern=r"\|\s+(?:\[(?P<domain>[\w\-\.]+)\]\((?P<url>https?:\/\/[\w\-\.\/]+)\)\s+)?\|\s+(?:\[(?:http:\/\/)?[\w\-\.\/\d]+\]\(http:\/\/(?P<onion>[\w\-\.\/\d]+\.onion\/?)\)\s+)?\|\s+(?:\[(?:http:\/\/)?[\w\-\.\/\d]+\]\(http:\/\/(?P<i2p>[\w\-\.\/\d]+\.i2p)\)\s+)?\|\s+(?P<notes>(?:[^\|])+)?\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/reddit/teddit/i2p", url="https://codeberg.org/teddit/teddit/raw/branch/main/README.md", regex_group="i2p", regex_pattern=r"\|\s+(?:\[(?P<domain>[\w\-\.]+)\]\((?P<url>https?:\/\/[\w\-\.\/]+)\)\s+)?\|\s+(?:\[(?:http:\/\/)?[\w\-\.\/\d]+\]\(http:\/\/(?P<onion>[\w\-\.\/\d]+\.onion\/?)\)\s+)?\|\s+(?:\[(?:http:\/\/)?[\w\-\.\/\d]+\]\(http:\/\/(?P<i2p>[\w\-\.\/\d]+\.i2p)\)\s+)?\|\s+(?P<notes>(?:[^\|])+)?\|"),
    # Libreddit
    RegexFromUrlInstance(relative_filepath_without_ext="instances/reddit/libreddit/instances", url="https://raw.githubusercontent.com/libreddit/libreddit/master/README.md", regex_pattern=r"\|\s+\[(?:(?P<onion>[\w\-\.\/\d]+\.onion)|(?P<domain>[\w\-\.\/\d]+))\]\((?P<url>https?:\/\/[\w\-\.\/\d]+)\)\s*(?:\(official\)\s+)?\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<cloudflare>(?:✅)?)\s\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/reddit/libreddit/onion", url="https://raw.githubusercontent.com/libreddit/libreddit/master/README.md", regex_group="onion", regex_pattern=r"\|\s+\[(?:(?P<onion>[\w\-\.\/\d]+\.onion)|(?P<domain>[\w\-\.\/\d]+))\]\((?P<url>https?:\/\/[\w\-\.\/\d]+)\)\s*(?:\(official\)\s+)?\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<cloudflare>(?:✅)?)\s\|"),
        # SearX
    JSONUsingCallableInstance(relative_filepath_without_ext="instances/search/searx/instances", url="https://searx.space/data/instances.json", json_handle=lambda raw: tuple(filter(lambda url: not any((".onion" in url, ".i2p" in url)), raw["instances"].keys()))),
    JSONUsingCallableInstance(relative_filepath_without_ext="instances/search/searx/onion", url="https://searx.space/data/instances.json", json_handle=lambda raw: tuple(filter(lambda url: ".onion" in url, raw["instances"].keys()))),
    JSONUsingCallableInstance(relative_filepath_without_ext="instances/search/searx/i2p", url="https://searx.space/data/instances.json", json_handle=lambda raw: tuple(filter(lambda url: ".i2p" in url, raw["instances"].keys()))),
    # Invidious
    JSONUsingCallableInstance(relative_filepath_without_ext="instances/youtube/invidious/instances", url="https://api.invidious.io/instances.json", json_handle=lambda raw: tuple(map(lambda inst: inst[0], tuple(filter(lambda inst: inst[1]["type"] == "https", raw))))),
    JSONUsingCallableInstance(relative_filepath_without_ext="instances/youtube/invidious/onion", url="https://api.invidious.io/instances.json", json_handle=lambda raw: tuple(map(lambda inst: inst[0], tuple(filter(lambda inst: inst[1]["type"] == "onion", raw))))),
    JSONUsingCallableInstance(relative_filepath_without_ext="instances/youtube/invidious/i2p", url="https://api.invidious.io/instances.json", json_handle=lambda raw: tuple(map(lambda inst: inst[0], tuple(filter(lambda inst: inst[1]["type"] == "i2p", raw))))),
    # HyperPipe (yt music)
    JSONUsingCallableInstance(relative_filepath_without_ext="instances/youtube/hyperpipe/instances", url="https://raw.codeberg.page/Hyperpipe/pages/api/frontend.json", json_handle=lambda raw: tuple(filter(lambda url: not any((".onion" in url, ".i2p" in url)), tuple(map(lambda inst: re.match(r"https?\:\/\/([^\/\s]*)\/?", inst['url']).groups()[0], raw))))),
    JSONUsingCallableInstance(relative_filepath_without_ext="instances/youtube/hyperpipe/onion", url="https://raw.codeberg.page/Hyperpipe/pages/api/frontend.json", json_handle=lambda raw: tuple(filter(lambda url: ".onion" in url, tuple(map(lambda inst: re.match(r"https?\:\/\/([^\/\s]*)\/?", inst['url']).groups()[0], raw))))),
    # WikiLess
    RegexCroppedFromUrlInstance(relative_filepath_without_ext="instances/wikipedia/wikiless/instances", crop_from="## Instances", crop_to="## TODO", regex_group="domain", url="https://gitea.slowb.ro/ticoombs/Wikiless/raw/branch/main/README.md", regex_pattern="\(https?:\/\/(?:(?P<i2p>[\w\-\.\/\d]+\.i2p)|(?P<onion>[\w\-\.\/\d]+\.onion)|(?P<domain>[\w\-\.\/\d]+))\)"),
    RegexCroppedFromUrlInstance(relative_filepath_without_ext="instances/wikipedia/wikiless/onion", crop_from="## Instances", crop_to="## TODO", regex_group="onion", url="https://gitea.slowb.ro/ticoombs/Wikiless/raw/branch/main/README.md", regex_pattern="\(https?:\/\/(?:(?P<i2p>[\w\-\.\/\d]+\.i2p)|(?P<onion>[\w\-\.\/\d]+\.onion)|(?P<domain>[\w\-\.\/\d]+))\)"),
    RegexCroppedFromUrlInstance(relative_filepath_without_ext="instances/wikipedia/wikiless/i2p", crop_from="## Instances", crop_to="## TODO", regex_group="i2p", url="https://gitea.slowb.ro/ticoombs/Wikiless/raw/branch/main/README.md", regex_pattern="\(https?:\/\/(?:(?P<i2p>[\w\-\.\/\d]+\.i2p)|(?P<onion>[\w\-\.\/\d]+\.onion)|(?P<domain>[\w\-\.\/\d]+))\)")
]


def main():
    for instance in INSTANCES:
        instance.from_instance().update()


if __name__ == "__main__":
    main()
