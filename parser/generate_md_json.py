import json
import os

try:
    from .consts import INST_FOLDER, Network
    from .main import HOME_PATH, INSTANCE_GROUPS, BaseInstance, InstancesGroupData
except ImportError:
    from consts import INST_FOLDER, Network
    from main import HOME_PATH, INSTANCE_GROUPS, BaseInstance, InstancesGroupData


def md_url_generator(data: BaseInstance, http=False):
    domains = data.load_from_json()
    protocol = "https://" if not http else "http://"
    for domain in domains:
        yield f"- [{domain}]({protocol + domain})"


def get_md_url(data, http=False):
    return tuple(md_url_generator(data, http))


def save_md(content, filepath):
    with open(filepath, mode="w+", encoding="utf-8") as f:
        f.write(content)


def save_json(obj, filepath):
    with open(filepath, mode="w+", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)


def create_instance_group_readme(metadata: InstancesGroupData, save=True, header=1):
    data = metadata.from_instance()
    md = ""
    for inst in data.instances:
        md += "#" * header
        md += {Network.CLEARNET: " Clearnet", Network.ONION: " Onion",
               Network.I2P: " I2P", Network.LOKI: " Loki"}[inst.relative_filepath_without_ext]
        md += "\n"
        md += "\n".join(get_md_url(inst, http=inst.relative_filepath_without_ext != Network.CLEARNET))
        md += "\n"
    if save:
        save_md(md, os.path.join(data.inst.get_folderpath(), "ReadMe.MD"))
    else:
        return md


def create_instance_group_json(metadata: InstancesGroupData):
    data = metadata.from_instance()
    json_raw = {inst.relative_filepath_without_ext: inst.load_from_json() for inst in data.instances}
    save_json(json_raw, os.path.join(data.inst.get_folderpath(), "all.json"))


def handle_instance(metadata):
    create_instance_group_readme(metadata)
    create_instance_group_json(metadata)


def create_all_json(groups_data):
    groups = [x.from_instance() for x in groups_data]
    json_raw = dict()
    for group in groups:
        json_raw[group.inst.get_name()] = {"name": group.inst.name, "url": group.inst.home_url}
        if group.inst.description:
            json_raw[group.inst.get_name()]["desc"] = group.inst.description
        for inst in group.instances:
            json_raw[group.inst.get_name()][inst.relative_filepath_without_ext] = inst.load_from_json()
    save_json(json_raw, os.path.join(HOME_PATH, INST_FOLDER, "all.json"))


def create_all_md(groups_data):
    groups = [x.from_instance() for x in groups_data]
    md = "# All Instances\n\n## Contents\n"
    md += "\n".join([f"- [{group.inst.name}](#{group.inst.get_name().replace(' ', '-')})" for group in groups])
    md += "\n"
    for group in groups:
        md += f"\n## {group.inst.name}\n\n{create_instance_group_readme(group.inst, save=False, header=3)}"
    save_md(md, os.path.join(HOME_PATH, INST_FOLDER, "all.md"))


if __name__ == "__main__":
    tuple(map(handle_instance, INSTANCE_GROUPS))
    create_all_json(INSTANCE_GROUPS)
    create_all_md(INSTANCE_GROUPS)
