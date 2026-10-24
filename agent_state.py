from typing import TypedDict, List


class AgentState(TypedDict):
    input: str
    zhihu_tcm_post_title: str
    zhihu_tcm_post_content: str
    zhihu_tcm_post_site: str
    zhihu_tcm_post_image_path_list: List[str]
    is_can_publish_zhihu_post: bool
    output: str
