from typing import TypedDict, Annotated, Sequence

from functools import lru_cache
from langchain_core.messages import BaseMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END, add_messages
from functools import lru_cache
from langgraph.prebuilt import ToolNode
from langchain.schema import AIMessage
import json
import requests
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import GenerationChunk
from typing import Optional, List, Dict, Mapping, Any, Iterator
from collections.abc import Generator
from langchain.llms.base import LLM
class XLLM(LLM):
    models: str
    model_variant: str = ''
    appid: str = 'maas_user02'
    appkey: str = "K2pTx4mF5oWQZBjcXLRD9PKl"
    url: str = "https://llm.xiaochuangai.com/v0.2/api/xiaochuang.ai"
    smart_qa: Any = None
    messages: List[Dict[str, str]] = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，我是xiaochuang.ai"}
    ]

    def __init__(self, **data):
        super().__init__(**data)
        # self.smart_qa = maas(self.url)
        # self.smart_qa.add_account(self.appid, self.appkey)

    @property
    def _llm_type(self) -> str:
        return "llm"

    def _construct_query(self, message: str, files="", models="", model_variant='', with_search=False) -> Dict:
        """构造请求体"""
        self.messages: List[Dict[str, str]] = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，我是xiaochuang.ai"}
        ]
        self.messages.append({"role": "user", "content": message})
        while len(self.messages) > 1:
            self.messages.pop(0)
        query = {
            "messages": self.messages,
            "file": files,
            "model": models,
            "model_variant": model_variant,
            "with_search_enhance": with_search,
        }
        return query
    def _clear_message(self):
        self.messages: List[Dict[str, str]] = []
    # def _construct_query(self, message: str, files="", models="", model_variant='', with_search=False) -> Dict:
    #     """构造请求体"""
    #     self.messages.append({"role": "user", "content": message})
    #     query = {
    #         "messages": self.messages,
    #         "file": files,
    #         "model": models,
    #         "model_variant": model_variant,
    #         "with_search_enhance": with_search,
    #     }
    #     return query


    @classmethod
    def _post(cls, url: str, query: Dict, appid='', appkey='') -> Any:
        def return_json(response):
            def is_valid_json(json_string):
                try:
                    json.loads(json_string)
                    return True
                except json.JSONDecodeError:
                    return False

            partial_message = ""
            buffer = ""
            file_path = 'data.csv'



            token = []
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    line = chunk.decode('utf-8')
                    buffer += line
                    if is_valid_json(buffer):
                        buffer_json = json.loads(buffer)
                        decoded_line_ = buffer_json["content"]
                        token = [buffer_json['total_tokens']]
                        partial_message += decoded_line_
                        yield decoded_line_
                        buffer = ""
                    else:
                        try:
                            str_ = "\r\n"
                            if str_ in buffer:
                                content_split = buffer.split(str_)
                                starti = 0
                                endi = len(content_split)
                                for content_i in content_split:
                                    starti += 1
                                    if content_i == "":
                                        buffer = ""
                                        continue
                                    if starti < endi:
                                        buffer_json = json.loads(content_i)
                                        decoded_line_ = buffer_json["content"]
                                        token = [buffer_json['total_tokens']]
                                        partial_message += decoded_line_
                                        yield decoded_line_
                                        buffer = ""

                                    elif starti == endi:
                                        if is_valid_json(content_i):
                                            buffer_json = json.loads(content_i)
                                            decoded_line_ = buffer_json["content"]
                                            token = [buffer_json['total_tokens']]
                                            partial_message += decoded_line_
                                            yield decoded_line_
                                            buffer = ""
                                        else:
                                            buffer = content_i
                            else:
                                continue
                        except Exception as e:
                            print(chunk, e)
                            pass

        _headers = {'Content-Type': 'application/json'}
        _headers["appid"] = appid
        _headers["api-key"] = appkey

        response = requests.post(url, headers=_headers, data=json.dumps(query), stream=True)
        result = return_json(response)
        return result

    def _call(self, message: str, stop: Optional[List[str]] = None, token_keys="xc-ltsF1ivfLvdectLtnQae3wXDQN",
              with_search=False, files="") -> str:
        query = self._construct_query(message=message, files=files, models=self.models,
                                      model_variant=self.model_variant, with_search=with_search)
        resp = self._post(url=self.url, query=query, appid=self.appid, appkey=self.appkey)

        total = ""
        if isinstance(resp, Generator):
            for i in resp:
                total += i
            return total
        elif resp.status_code == 200:
            return resp
        else:
            return "请求模型失败"

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"url": self.url}

    def _stream(self, message: str, stop: Optional[List[str]] = None, token_keys="xc-ltsF1ivfLvdectLtnQae3wXDQN",
                with_search=False, files="", run_manager: Optional[CallbackManagerForLLMRun] = None) -> Iterator[
        GenerationChunk]:
        query = self._construct_query(message=message, files=files, models=self.models,
                                      model_variant=self.model_variant, with_search=with_search)
        resps = self._post(url=self.url, query=query, appid=self.appid, appkey=self.appkey)
        str = ''
        for resp in resps:
            str += resp
            yield GenerationChunk(text=resp)
        print('query',query,'output',str)
tools = [TavilySearchResults(max_results=1)]

@lru_cache(maxsize=4)
def _get_model(model_name: str):
    model = XLLM(models='deepseek')
    return model


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there are no tool calls, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define the function that calls the model
def call_model(state, config):
    messages = state["messages"]
    messages = [{"role": "system", "content": system_prompt}] + messages
    model_name = config.get('configurable', {}).get("model_name", "anthropic")
    model = _get_model(model_name)
    content = model.invoke(messages)

    ###
    additional_kwargs = {'refusal': None}
    response_metadata = {
        'token_usage': {
            'completion_tokens': 36,
            'prompt_tokens': 87,
            'total_tokens': 123,
            'completion_tokens_details': None,
            'prompt_tokens_details': None
        },
        'model_name': 'gpt-35-turbo',
        'system_fingerprint': 'fp_808245b034',
        'finish_reason': 'stop',
        'logprobs': None
    }
    id_value = 'run-762224c4-60df-4725-9e78-ca01a9e88996-0'
    usage_metadata = {
        'input_tokens': 87,
        'output_tokens': 36,
        'total_tokens': 123,
        'input_token_details': {},
        'output_token_details': {}
    }
    ###
        # 创建AIMessage对象
    ai_message = AIMessage(
        content=content,
        additional_kwargs=additional_kwargs,
        response_metadata=response_metadata,
        id=id_value,
        usage_metadata=usage_metadata
    )

    # We return a list, because this will get added to the existing list
    return {"messages": [ai_message]}


# Define the function to execute tools
tool_node = ToolNode(tools)


# Define a new graph
workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
graph = workflow.compile()
