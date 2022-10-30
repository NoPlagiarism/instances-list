import json
import os
import re
import urllib.request
from dataclasses import dataclass

HOME_PATH = os.path.dirname(os.path.dirname(__file__))


def get_str_from_url(url):
    with urllib.request.urlopen(url) as res:
        return res.read().decode(res.headers.get_content_charset("utf-8"))


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
            domain_list.append(match.groupdict()["domain"])
        return sorted(domain_list)
    
    def get_all_domains(self):
        text = get_str_from_url(self.inst.url)
        domain_list = self.get_all_domains_from_text(text)
        return domain_list


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
        raw = get_str_from_url(self.inst.url)
        domain_list = raw.strip("\n").split("\n")
        domain_list.sort()
        return domain_list


INSTANCES = [
    # ProxiTok
    RegexFromUrlInstance(relative_filepath_without_ext="instances/proxitok/instances", url="https://raw.githubusercontent.com/wiki/pablouser1/ProxiTok/Public-instances.md", regex_pattern=r"\|\s+\[(?P<domain>(?:\w|\.)+)\]\((?P<url>https?:\/\/(?:\w|\.)+)\)\s+(?:\(Official\)\s+)?\|\s+(?P<cloudflare>Yes|No)\s+\|\s+(?P<flagemoji>\S+)\s+\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/proxitok/onion", url="https://raw.githubusercontent.com/wiki/pablouser1/ProxiTok/Public-instances.md", regex_pattern=r"\|\s+\[(?P<domain>(?:\w|\.)+\.onion)\]\((?P<url>https?:\/\/(?:\w|\.)+)\)\s+\|"),
    # SimplyTranslate
    JustFromUrlInstance(relative_filepath_without_ext="instances/simplytranslate/instance", url="https://simple-web.org/instances/simplytranslate"),
    JustFromUrlInstance(relative_filepath_without_ext="instances/simplytranslate/onion", url="https://simple-web.org/instances/simplytranslate_onion"),
    JustFromUrlInstance(relative_filepath_without_ext="instances/simplytranslate/i2p", url="https://simple-web.org/instances/simplytranslate_i2p"),
    JustFromUrlInstance(relative_filepath_without_ext="instances/simplytranslate/loki", url="https://simple-web.org/instances/simplytranslate_loki"),
    # Whoogle
    RegexFromUrlInstance(relative_filepath_without_ext="instances/whoogle/instances", url="https://raw.githubusercontent.com/benbusby/whoogle-search/main/README.md", regex_pattern=r"\|\s+\[https?:\/\/(?P<domain>(?:\w|\.)+)\]\((?P<url>https?:\/\/(?:\w|\.)+)\/?\)\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<language>\S+)\s+\|\s?(?P<cloudflare>(?:✅\s|\s))\|$"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/whoogle/onion", url="https://raw.githubusercontent.com/benbusby/whoogle-search/main/README.md", regex_pattern=r"\|?\s+\[https?:\/\/(?P<domain>(?:\w|\.)+)\.onion\]\((?P<url>https?:\/\/(?:\w|\.)+)\/?\)\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<language>\S+)\s+\|"),
    RegexFromUrlInstance(relative_filepath_without_ext="instances/whoogle/i2p", url="https://raw.githubusercontent.com/benbusby/whoogle-search/main/README.md", regex_pattern=r"\|?\s+\[https?:\/\/(?P<domain>(?:\w|\.)+)\.i2p\]\((?P<url>https?:\/\/(?:\w|\.)+)\/?\)\s+\|\s+(?P<flagemoji>\W+)\s+(?P<country>\w+)\s+\|\s+(?P<language>\S+)\s+\|")
]


def main():
    for instance in INSTANCES:
        instance.from_instance().update()


if __name__ == "__main__":
    main()
