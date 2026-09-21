"""Load Rapid SCADA channel metadata from BaseXML Cnl.xml."""
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache

from .config import get_settings


@dataclass
class ChannelMeta:
    cnl_num: int
    name: str
    tag_code: str | None = None


@lru_cache
def load_channel_map() -> dict[int, ChannelMeta]:
    path = get_settings().channel_map_path
    if not path or not os.path.exists(path):
        return {}

    tree = ET.parse(path)
    root = tree.getroot()
    result: dict[int, ChannelMeta] = {}
    for cnl in root.findall("Cnl"):
        cnl_num_el = cnl.find("CnlNum")
        name_el = cnl.find("Name")
        tag_code_el = cnl.find("TagCode")
        if cnl_num_el is None or name_el is None:
            continue
        try:
            cnl_num = int(cnl_num_el.text or "0")
        except ValueError:
            continue
        result[cnl_num] = ChannelMeta(
            cnl_num=cnl_num,
            name=name_el.text or "",
            tag_code=tag_code_el.text if tag_code_el is not None else None,
        )
    return result


def resolve_cnl_num(identifier: str | int) -> int | None:
    """Resolve a channel number from an integer or a TagCode string."""
    if isinstance(identifier, int):
        return identifier
    try:
        return int(identifier)
    except (ValueError, TypeError):
        pass

    channel_map = load_channel_map()
    for meta in channel_map.values():
        if meta.tag_code == identifier:
            return meta.cnl_num
    return None


def enrich_current_values(rows: list[dict]) -> list[dict]:
    """Add name/tag_code to current value rows when metadata is available."""
    channel_map = load_channel_map()
    enriched = []
    for row in rows:
        meta = channel_map.get(row["cnl_num"])
        enriched.append(
            {
                **row,
                "name": meta.name if meta else None,
                "tag_code": meta.tag_code if meta else None,
            }
        )
    return enriched
