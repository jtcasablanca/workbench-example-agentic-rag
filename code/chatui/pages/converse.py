# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

### This module contains the chatui gui for having a conversation. ###

import functools
from typing import Any, Dict, List, Tuple, Union

import gradio as gr
import shutil
import os
import subprocess
import time
import sys
import json

INTERNAL_API = os.getenv('INTERNAL_API', '')

# Model identifiers with prefix
LLAMA = "meta/llama3-70b-instruct"
MISTRAL = "mistralai/mixtral-8x22b-instruct-v0.1"



if INTERNAL_API != '':
    LLAMA = f'{INTERNAL_API}/meta/llama-3.1-70b-instruct'  
    MISTRAL = f'{INTERNAL_API}/mistralai/mixtral-8x22b-instruct-v0.1'



from chatui import assets, chat_client
from chatui.prompts import prompts_llama3, prompts_mistral
from chatui.utils import compile, database, logger, gpu_compatibility

from langgraph.graph import END, StateGraph

PATH = "/"
TITLE = "Agentic RAG: Chat UI"
OUTPUT_TOKENS = 250
MAX_DOCS = 5

### Load in CSS here for components that need custom styling. ###

_LOCAL_CSS = """
#contextbox {
    overflow-y: scroll !important;
    max-height: 400px;
}

#params .tabs {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}
#params .tabitem[style="display: block;"] {
    flex-grow: 1;
    display: flex !important;
}
#params .gap {
    flex-grow: 1;
}
#params .form {
    flex-grow: 1 !important;
}
#params .form > :last-child{
    flex-grow: 1;
}
#accordion {
}
#rag-inputs .svelte-1gfkn6j {
    color: #76b900;
}
#rag-inputs .svelte-s1r2yt {
    color: #76b900;
}
"""

sys.stdout = logger.Logger("/project/code/output.log")

def build_page(client: chat_client.ChatClient) -> gr.Blocks:
    """
    Build the gradio page to be mounted in the frame.
    
    Parameters: 
        client (chat_client.ChatClient): The chat client running the application. 
    
    Returns:
        page (gr.Blocks): A Gradio page.
    """
    kui_theme, kui_styles = assets.load_theme("kaizen")
    
    """ Compile the agentic graph. """
    
    workflow = compile.compile_graph()
    app = workflow.compile()

    """ List of currently supported models. """
    
    model_list = [LLAMA, MISTRAL]

    with gr.Blocks(title=TITLE, theme=kui_theme, css=kui_styles + _LOCAL_CSS) as page:
        gr.Markdown(f"# {TITLE}")

        """ Keep state of which queries need to use NIMs vs API Endpoints. """
        
        router_use_nim = gr.State(False)
        retrieval_use_nim = gr.State(False)
        generator_use_nim = gr.State(False)
        hallucination_use_nim = gr.State(False)
        answer_use_nim = gr.State(False)

        """ Build the Chat Application. """
        
        with gr.Row(equal_height=True):

            # Left Column will display the chatbot
            with gr.Column(scale=15, min_width=350):

                # Diagram of the agentic websearch RAG workflow
                with gr.Row():
                    agentic_flow = gr.Image("/project/code/chatui/static/agentic-flow.png", 
                                            show_label=False,
                                            show_download_button=False,
                                            interactive=False)
                
                # Main chatbot panel. 
                with gr.Row(equal_height=True):
                    with gr.Column(min_width=350):
                        chatbot = gr.Chatbot(show_label=False)

                # Message box for user input
                with gr.Row(equal_height=True):
                    with gr.Column(scale=3, min_width=450):
                        msg = gr.Textbox(
                            show_label=False,
                            placeholder="Enter text and press ENTER",
                            container=False,
                            interactive=True,
                        )

                    with gr.Column(scale=1, min_width=150):
                        _ = gr.ClearButton([msg, chatbot], value="Clear history")
            
            # Hidden column to be rendered when the user collapses all settings.
            with gr.Column(scale=1, min_width=100, visible=False) as hidden_settings_column:
                show_settings = gr.Button(value="< Expand", size="sm")
            
            # Right column to display all relevant settings
            with gr.Column(scale=10, min_width=350) as settings_column:
                with gr.Tabs(selected=0) as settings_tabs:

                    # Settings for each component model of the agentic workflow
                    with gr.TabItem("Models", id=0) as agent_settings:
    
                        ########################
                        ##### ROUTER MODEL #####
                        ########################
                        router_btn = gr.Button("Router", variant="sm")
                        with gr.Group(visible=False) as group_router:
                            with gr.Tabs(selected=0) as router_tabs:
                                with gr.TabItem("API Endpoints", id=0) as router_api:
                                    model_router = gr.Dropdown(model_list, 
                                                               value=model_list[0],
                                                               label="Select a Model",
                                                               elem_id="rag-inputs", 
                                                               interactive=True)
                                    
                                with gr.TabItem("NIM Endpoints", id=1) as router_nim:
                                    with gr.Row():
                                        nim_router_gpu_type = gr.Dropdown(
                                            choices=gpu_compatibility.get_gpu_types(),
                                            label="GPU Type",
                                            info="Select your GPU type",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_router_gpu_count = gr.Dropdown(
                                            choices=[],
                                            label="Number of GPUs",
                                            info="Select number of GPUs",
                                            elem_id="rag-inputs",
                                            scale=1,
                                            interactive=False
                                        )
                                    
                                    with gr.Row():
                                        nim_router_ip = gr.Textbox(
                                            placeholder="10.123.45.678",
                                            label="Microservice Host",
                                            info="IP Address running the microservice",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_router_port = gr.Textbox(
                                            placeholder="8000",
                                            label="Port",
                                            info="Optional, (default: 8000)",
                                            elem_id="rag-inputs",
                                            scale=1
                                        )
                                    
                                    nim_router_id = gr.Dropdown(
                                        choices=[],
                                        label="Model running in microservice",
                                        info="Select a compatible model for your GPU configuration",
                                        elem_id="rag-inputs",
                                        interactive=False
                                    )

                                    # Add warning box for compatibility issues
                                    nim_router_warning = gr.Markdown(visible=False, value="")

                                with gr.TabItem("Hide", id=2) as router_hide:
                                    gr.Markdown("")

                            with gr.Accordion("Configure the Router Prompt", 
                                              elem_id="rag-inputs", open=False) as accordion_router:
                                prompt_router = gr.Textbox(value=prompts_llama3.router_prompt,
                                                           lines=12,
                                                           show_label=False,
                                                           interactive=True)
    
                        ##################################
                        ##### RETRIEVAL GRADER MODEL #####
                        ##################################
                        retrieval_btn = gr.Button("Retrieval Grader", variant="sm")
                        with gr.Group(visible=False) as group_retrieval:
                            with gr.Tabs(selected=0) as retrieval_tabs:
                                with gr.TabItem("API Endpoints", id=0) as retrieval_api:
                                    model_retrieval = gr.Dropdown(model_list, 
                                                                         value=model_list[0],
                                                                         label="Select a Model",
                                                                         elem_id="rag-inputs", 
                                                                         interactive=True)
                                with gr.TabItem("NIM Endpoints", id=1) as retrieval_nim:
                                    with gr.Row():
                                        nim_retrieval_gpu_type = gr.Dropdown(
                                            choices=gpu_compatibility.get_gpu_types(),
                                            label="GPU Type",
                                            info="Select your GPU type",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_retrieval_gpu_count = gr.Dropdown(
                                            choices=[],
                                            label="Number of GPUs",
                                            info="Select number of GPUs",
                                            elem_id="rag-inputs",
                                            scale=1,
                                            interactive=False
                                        )
                                    
                                    with gr.Row():
                                        nim_retrieval_ip = gr.Textbox(
                                            placeholder="10.123.45.678",
                                            label="Microservice Host",
                                            info="IP Address running the microservice",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_retrieval_port = gr.Textbox(
                                            placeholder="8000",
                                            label="Port",
                                            info="Optional, (default: 8000)",
                                            elem_id="rag-inputs",
                                            scale=1
                                        )
                                    
                                    nim_retrieval_id = gr.Dropdown(
                                        choices=[],
                                        label="Model running in microservice",
                                        info="Select a compatible model for your GPU configuration",
                                        elem_id="rag-inputs",
                                        interactive=False
                                    )

                                    # Add warning box for compatibility issues
                                    nim_retrieval_warning = gr.Markdown(visible=False, value="")

                                with gr.TabItem("Hide", id=2) as retrieval_hide:
                                    gr.Markdown("")
                            
                            with gr.Accordion("Configure the Retrieval Grader Prompt", 
                                              elem_id="rag-inputs", open=False) as accordion_retrieval:
                                prompt_retrieval = gr.Textbox(value=prompts_llama3.retrieval_prompt,
                                                                     lines=21,
                                                                     show_label=False,
                                                                     interactive=True)
    
                        ###########################
                        ##### GENERATOR MODEL #####
                        ###########################
                        generator_btn = gr.Button("Generator", variant="sm")
                        with gr.Group(visible=False) as group_generator:
                            with gr.Tabs(selected=0) as generator_tabs:
                                with gr.TabItem("API Endpoints", id=0) as generator_api:
                                    model_generator = gr.Dropdown(model_list, 
                                                                  value=model_list[0],
                                                                  label="Select a Model",
                                                                  elem_id="rag-inputs", 
                                                                  interactive=True)
                                with gr.TabItem("NIM Endpoints", id=1) as generator_nim:
                                    with gr.Row():
                                        nim_generator_gpu_type = gr.Dropdown(
                                            choices=gpu_compatibility.get_gpu_types(),
                                            label="GPU Type",
                                            info="Select your GPU type",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_generator_gpu_count = gr.Dropdown(
                                            choices=[],
                                            label="Number of GPUs",
                                            info="Select number of GPUs",
                                            elem_id="rag-inputs",
                                            scale=1,
                                            interactive=False
                                        )
                                    
                                    with gr.Row():
                                        nim_generator_ip = gr.Textbox(
                                            placeholder="10.123.45.678",
                                            label="Microservice Host",
                                            info="IP Address running the microservice",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_generator_port = gr.Textbox(
                                            placeholder="8000",
                                            label="Port",
                                            info="Optional, (default: 8000)",
                                            elem_id="rag-inputs",
                                            scale=1
                                        )
                                    
                                    nim_generator_id = gr.Dropdown(
                                        choices=[],
                                        label="Model running in microservice",
                                        info="Select a compatible model for your GPU configuration",
                                        elem_id="rag-inputs",
                                        interactive=False
                                    )

                                    # Add warning box for compatibility issues
                                    nim_generator_warning = gr.Markdown(visible=False, value="")

                                with gr.TabItem("Hide", id=2) as generator_hide:
                                    gr.Markdown("")
                            
                            with gr.Accordion("Configure the Generator Prompt", 
                                              elem_id="rag-inputs", open=False) as accordion_generator:
                                prompt_generator = gr.Textbox(value=prompts_llama3.generator_prompt,
                                                          lines=15,
                                                          show_label=False,
                                                          interactive=True)
    
                        ######################################
                        ##### HALLUCINATION GRADER MODEL #####
                        ######################################
                        hallucination_btn = gr.Button("Hallucination Grader", variant="sm")
                        with gr.Group(visible=False) as group_hallucination:
                            with gr.Tabs(selected=0) as hallucination_tabs:
                                with gr.TabItem("API Endpoints", id=0) as hallucination_api:
                                    model_hallucination = gr.Dropdown(model_list, 
                                                                             value=model_list[0],
                                                                             label="Select a Model",
                                                                             elem_id="rag-inputs", 
                                                                             interactive=True)
                                with gr.TabItem("NIM Endpoints", id=1) as hallucination_nim:
                                    with gr.Row():
                                        nim_hallucination_gpu_type = gr.Dropdown(
                                            choices=gpu_compatibility.get_gpu_types(),
                                            label="GPU Type",
                                            info="Select your GPU type",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_hallucination_gpu_count = gr.Dropdown(
                                            choices=[],
                                            label="Number of GPUs",
                                            info="Select number of GPUs",
                                            elem_id="rag-inputs",
                                            scale=1,
                                            interactive=False
                                        )
                                    
                                    with gr.Row():
                                        nim_hallucination_ip = gr.Textbox(
                                            placeholder="10.123.45.678",
                                            label="Microservice Host",
                                            info="IP Address running the microservice",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_hallucination_port = gr.Textbox(
                                            placeholder="8000",
                                            label="Port",
                                            info="Optional, (default: 8000)",
                                            elem_id="rag-inputs",
                                            scale=1
                                        )
                                    
                                    nim_hallucination_id = gr.Dropdown(
                                        choices=[],
                                        label="Model running in microservice",
                                        info="Select a compatible model for your GPU configuration",
                                        elem_id="rag-inputs",
                                        interactive=False
                                    )

                                    # Add warning box for compatibility issues
                                    nim_hallucination_warning = gr.Markdown(visible=False, value="")

                                with gr.TabItem("Hide", id=2) as hallucination_hide:
                                    gr.Markdown("")
                            
                            with gr.Accordion("Configure the Hallucination Prompt", 
                                              elem_id="rag-inputs", open=False) as accordion_hallucination:
                                prompt_hallucination = gr.Textbox(value=prompts_llama3.hallucination_prompt,
                                                                         lines=17,
                                                                         show_label=False,
                                                                         interactive=True)
    
                        ###############################
                        ##### ANSWER GRADER MODEL #####
                        ###############################
                        answer_btn = gr.Button("Answer Grader", variant="sm")
                        with gr.Group(visible=False) as group_answer:
                            with gr.Tabs(selected=0) as answer_tabs:
                                with gr.TabItem("API Endpoints", id=0) as answer_api:
                                    model_answer = gr.Dropdown(model_list, 
                                                                      value=model_list[0],
                                                                      elem_id="rag-inputs",
                                                                      label="Select a Model",
                                                                      interactive=True)
                                with gr.TabItem("NIM Endpoints", id=1) as answer_nim:
                                    with gr.Row():
                                        nim_answer_gpu_type = gr.Dropdown(
                                            choices=gpu_compatibility.get_gpu_types(),
                                            label="GPU Type",
                                            info="Select your GPU type",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_answer_gpu_count = gr.Dropdown(
                                            choices=[],
                                            label="Number of GPUs",
                                            info="Select number of GPUs",
                                            elem_id="rag-inputs",
                                            scale=1,
                                            interactive=False
                                        )
                                    
                                    with gr.Row():
                                        nim_answer_ip = gr.Textbox(
                                            placeholder="10.123.45.678",
                                            label="Microservice Host",
                                            info="IP Address running the microservice",
                                            elem_id="rag-inputs",
                                            scale=2
                                        )
                                        nim_answer_port = gr.Textbox(
                                            placeholder="8000",
                                            label="Port",
                                            info="Optional, (default: 8000)",
                                            elem_id="rag-inputs",
                                            scale=1
                                        )
                                    
                                    nim_answer_id = gr.Dropdown(
                                        choices=[],
                                        label="Model running in microservice",
                                        info="Select a compatible model for your GPU configuration",
                                        elem_id="rag-inputs",
                                        interactive=False
                                    )

                                    # Add warning box for compatibility issues
                                    nim_answer_warning = gr.Markdown(visible=False, value="")

                                with gr.TabItem("Hide", id=2) as answer_hide:
                                    gr.Markdown("")
                                    
                            with gr.Accordion("Configure the Answer Prompt", 
                                              elem_id="rag-inputs", open=False) as accordion_answer:
                                prompt_answer = gr.Textbox(value=prompts_llama3.answer_prompt,
                                                                  lines=17,
                                                                  show_label=False,
                                                                  interactive=True)
                        
                    # Second tab item is for uploading to and clearing the vector database
                    with gr.TabItem("Documents", id=1) as document_settings:
                        gr.Markdown("")
                        gr.Markdown("Upload webpages or PDF files to be stored persistently in the vector database.\n")
                        with gr.Tabs(selected=0) as document_tabs:
                            with gr.TabItem("Webpages", id=0) as url_tab:
                                url_docs = gr.Textbox(value="https://lilianweng.github.io/posts/2023-06-23-agent/\nhttps://lilianweng.github.io/posts/2023-03-15-prompt-engineering/\nhttps://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
                                                      lines=5, 
                                                      info="Enter a list of URLs, one per line", 
                                                      show_label=False, 
                                                      interactive=True)
                            
                                with gr.Row():
                                    url_docs_upload = gr.Button(value="Upload Docs")
                                    url_docs_clear = gr.Button(value="Clear Docs")

                            with gr.TabItem("PDFs", id=1) as pdf_tab:
                                pdf_docs_upload = gr.File(interactive=True, 
                                                          show_label=False, 
                                                          file_types=[".pdf"], 
                                                          file_count="multiple")
                                pdf_docs_clear = gr.Button(value="Clear Docs")
    
                    # Third tab item is for the actions output console. 
                    with gr.TabItem("Monitor", id=2) as console_settings:
                        gr.Markdown("")
                        gr.Markdown("Monitor agentic actions and view the pipeline trace of the latest response.\n")
                        with gr.Tabs(selected=0) as console_tabs:
                            with gr.TabItem("Actions Console", id=0) as actions_tab:
                                logs = gr.Textbox(show_label=False, lines=24, max_lines=24, interactive=False)
                            with gr.TabItem("Response Trace", id=1) as trace_tab:
                                actions = gr.JSON(
                                    scale=1,
                                    show_label=False,
                                    visible=True,
                                    elem_id="contextbox",
                                )
                    
                    # Third tab item is for collapsing the entire settings pane for readability. 
                    with gr.TabItem("Hide All Settings", id=3) as hide_all_settings:
                        gr.Markdown("")

        page.load(logger.read_logs, None, logs, every=1)

        """ These helper functions hide the expanded component model settings when the Hide tab is clicked. """
        
        def _toggle_hide_router():
            return {
                group_router: gr.update(visible=False),
                router_tabs: gr.update(selected=0),
                router_btn: gr.update(visible=True),
            }

        def _toggle_hide_retrieval():
            return {
                group_retrieval: gr.update(visible=False),
                retrieval_tabs: gr.update(selected=0),
                retrieval_btn: gr.update(visible=True),
            }

        def _toggle_hide_generator():
            return {
                group_generator: gr.update(visible=False),
                generator_tabs: gr.update(selected=0),
                generator_btn: gr.update(visible=True),
            }

        def _toggle_hide_hallucination():
            return {
                group_hallucination: gr.update(visible=False),
                hallucination_tabs: gr.update(selected=0),
                hallucination_btn: gr.update(visible=True),
            }

        def _toggle_hide_answer():
            return {
                group_answer: gr.update(visible=False),
                answer_tabs: gr.update(selected=0),
                answer_btn: gr.update(visible=True),
            }

        router_hide.select(_toggle_hide_router, None, [group_router, router_tabs, router_btn])
        retrieval_hide.select(_toggle_hide_retrieval, None, [group_retrieval, retrieval_tabs, retrieval_btn])
        generator_hide.select(_toggle_hide_generator, None, [group_generator, generator_tabs, generator_btn])
        hallucination_hide.select(_toggle_hide_hallucination, None, [group_hallucination, hallucination_tabs, hallucination_btn])
        answer_hide.select(_toggle_hide_answer, None, [group_answer, answer_tabs, answer_btn])

        """ These helper functions set state and prompts when either the NIM or API Endpoint tabs are selected. """
        
        def _update_gpu_counts(component: str, gpu_type: str):
            """Update the available GPU counts for selected GPU type."""
            counts = gpu_compatibility.get_supported_gpu_counts(gpu_type)
            components = {
                "router": [nim_router_gpu_count, nim_router_id, nim_router_warning],
                "retrieval": [nim_retrieval_gpu_count, nim_retrieval_id, nim_retrieval_warning],
                "generator": [nim_generator_gpu_count, nim_generator_id, nim_generator_warning],
                "hallucination": [nim_hallucination_gpu_count, nim_hallucination_id, nim_hallucination_warning],
                "answer": [nim_answer_gpu_count, nim_answer_id, nim_answer_warning]
            }
            return {
                components[component][0]: gr.update(choices=counts, value=None, interactive=True),
                components[component][1]: gr.update(choices=[], value=None, interactive=False),
                components[component][2]: gr.update(visible=False, value="")
            }
        
        def _update_compatible_models(component: str, gpu_type: str, num_gpus: str):
            """Update the compatible models list based on GPU configuration."""
            if not gpu_type or not num_gpus:
                components = {
                    "router": [nim_router_id, nim_router_warning],
                    "retrieval": [nim_retrieval_id, nim_retrieval_warning],
                    "generator": [nim_generator_id, nim_generator_warning],
                    "hallucination": [nim_hallucination_id, nim_hallucination_warning],
                    "answer": [nim_answer_id, nim_answer_warning]
                }
                return {
                    components[component][0]: gr.update(choices=[], value=None, interactive=False),
                    components[component][1]: gr.update(visible=False, value="")
                }
            
            compatibility = gpu_compatibility.get_compatible_models(gpu_type, num_gpus)
            
            if compatibility["warning_message"]:
                components = {
                    "router": [nim_router_id, nim_router_warning],
                    "retrieval": [nim_retrieval_id, nim_retrieval_warning],
                    "generator": [nim_generator_id, nim_generator_warning],
                    "hallucination": [nim_hallucination_id, nim_hallucination_warning],
                    "answer": [nim_answer_id, nim_answer_warning]
                }
                return {
                    components[component][0]: gr.update(choices=[], value=None, interactive=False),
                    components[component][1]: gr.update(visible=True, value=f"⚠️ {compatibility['warning_message']}")
                }
            
            components = {
                "router": [nim_router_id, nim_router_warning],
                "retrieval": [nim_retrieval_id, nim_retrieval_warning],
                "generator": [nim_generator_id, nim_generator_warning],
                "hallucination": [nim_hallucination_id, nim_hallucination_warning],
                "answer": [nim_answer_id, nim_answer_warning]
            }
            return {
                components[component][0]: gr.update(
                    choices=compatibility["compatible_models"],
                    value=compatibility["compatible_models"][0] if compatibility["compatible_models"] else None,
                    interactive=True
                ),
                components[component][1]: gr.update(visible=False, value="")
            }

        # Add the event handlers for all components
        nim_router_gpu_type.change(lambda x: _update_gpu_counts("router", x), nim_router_gpu_type, 
                                 [nim_router_gpu_count, nim_router_id, nim_router_warning])
        nim_router_gpu_count.change(lambda x, y: _update_compatible_models("router", x, y), 
                                  [nim_router_gpu_type, nim_router_gpu_count], 
                                  [nim_router_id, nim_router_warning])

        nim_retrieval_gpu_type.change(lambda x: _update_gpu_counts("retrieval", x), nim_retrieval_gpu_type, 
                                    [nim_retrieval_gpu_count, nim_retrieval_id, nim_retrieval_warning])
        nim_retrieval_gpu_count.change(lambda x, y: _update_compatible_models("retrieval", x, y), 
                                     [nim_retrieval_gpu_type, nim_retrieval_gpu_count], 
                                     [nim_retrieval_id, nim_retrieval_warning])

        nim_generator_gpu_type.change(lambda x: _update_gpu_counts("generator", x), nim_generator_gpu_type, 
                                    [nim_generator_gpu_count, nim_generator_id, nim_generator_warning])
        nim_generator_gpu_count.change(lambda x, y: _update_compatible_models("generator", x, y), 
                                     [nim_generator_gpu_type, nim_generator_gpu_count], 
                                     [nim_generator_id, nim_generator_warning])

        nim_hallucination_gpu_type.change(lambda x: _update_gpu_counts("hallucination", x), nim_hallucination_gpu_type, 
                                        [nim_hallucination_gpu_count, nim_hallucination_id, nim_hallucination_warning])
        nim_hallucination_gpu_count.change(lambda x, y: _update_compatible_models("hallucination", x, y), 
                                         [nim_hallucination_gpu_type, nim_hallucination_gpu_count], 
                                         [nim_hallucination_id, nim_hallucination_warning])

        nim_answer_gpu_type.change(lambda x: _update_gpu_counts("answer", x), nim_answer_gpu_type, 
                                 [nim_answer_gpu_count, nim_answer_id, nim_answer_warning])
        nim_answer_gpu_count.change(lambda x, y: _update_compatible_models("answer", x, y), 
                                  [nim_answer_gpu_type, nim_answer_gpu_count], 
                                  [nim_answer_id, nim_answer_warning])

        """ These helper functions track the API Endpoint selected and regenerates the prompt accordingly. """
        
        def _toggle_model_router(selected_model: str):
            match selected_model:
                case str() if selected_model == LLAMA:
                    return gr.update(value=prompts_llama3.router_prompt)
                case str() if selected_model == MISTRAL:
                    return gr.update(value=prompts_mistral.router_prompt)
                case _:
                    return gr.update(value=prompts_llama3.router_prompt)
        
        def _toggle_model_retrieval(selected_model: str):
            match selected_model:
                case str() if selected_model == LLAMA:
                    return gr.update(value=prompts_llama3.retrieval_prompt)
                case str() if selected_model == MISTRAL:
                    return gr.update(value=prompts_mistral.retrieval_prompt)
                case _:
                    return gr.update(value=prompts_llama3.retrieval_prompt)

        def _toggle_model_generator(selected_model: str):
            match selected_model:
                case str() if selected_model == LLAMA:
                    return gr.update(value=prompts_llama3.generator_prompt)
                case str() if selected_model == MISTRAL:
                    return gr.update(value=prompts_mistral.generator_prompt)
                case _:
                    return gr.update(value=prompts_llama3.generator_prompt)
            
        def _toggle_model_hallucination(selected_model: str):
            match selected_model:
                case str() if selected_model == LLAMA:
                    return gr.update(value=prompts_llama3.hallucination_prompt)
                case str() if selected_model == MISTRAL:
                    return gr.update(value=prompts_mistral.hallucination_prompt)
                case _:
                    return gr.update(value=prompts_llama3.hallucination_prompt)
            
        def _toggle_model_answer(selected_model: str):
            match selected_model:
                case str() if selected_model == LLAMA:
                    return gr.update(value=prompts_llama3.answer_prompt)
                case str() if selected_model == MISTRAL:
                    return gr.update(value=prompts_mistral.answer_prompt)
                case _:
                    return gr.update(value=prompts_llama3.answer_prompt)
            
        model_router.change(_toggle_model_router, [model_router], [prompt_router])
        model_retrieval.change(_toggle_model_retrieval, [model_retrieval], [prompt_retrieval])
        model_generator.change(_toggle_model_generator, [model_generator], [prompt_generator])
        model_hallucination.change(_toggle_model_hallucination, [model_hallucination], [prompt_hallucination])
        model_answer.change(_toggle_model_answer, [model_answer], [prompt_answer])
        
        """ These helper functions upload and clear the documents and webpages to/from the ChromaDB. """

        def _upload_documents_pdf(files, progress=gr.Progress()):
            progress(0.25, desc="Initializing Task")
            time.sleep(0.75)
            progress(0.5, desc="Uploading Docs")
            database.upload_pdf(files)
            progress(0.75, desc="Cleaning Up")
            time.sleep(0.75)
            return {
                url_docs_clear: gr.update(value="Clear Docs", variant="secondary", interactive=True),
                pdf_docs_clear: gr.update(value="Clear Docs", variant="secondary", interactive=True),
                agentic_flow: gr.update(visible=True),
            }

        def _upload_documents(docs: str, progress=gr.Progress()):
            progress(0.2, desc="Initializing Task")
            time.sleep(0.75)
            progress(0.4, desc="Processing URL List")
            docs_list = docs.splitlines()
            progress(0.6, desc="Uploading Docs")
            database.upload(docs_list)
            progress(0.8, desc="Cleaning Up")
            time.sleep(0.75)
            return {
                url_docs_upload: gr.update(value="Docs Uploaded", variant="primary", interactive=False),
                url_docs_clear: gr.update(value="Clear Docs", variant="secondary", interactive=True),
                pdf_docs_clear: gr.update(value="Clear Docs", variant="secondary", interactive=True),
                agentic_flow: gr.update(visible=True),
            }

        def _clear_documents(progress=gr.Progress()):
            progress(0.25, desc="Initializing Task")
            time.sleep(0.75)
            progress(0.5, desc="Clearing Database")
            database.clear()
            progress(0.75, desc="Cleaning Up")
            time.sleep(0.75)
            return {
                url_docs_upload: gr.update(value="Upload Docs", variant="secondary", interactive=True),
                url_docs_clear: gr.update(value="Docs Cleared", variant="primary", interactive=False),
                pdf_docs_upload: gr.update(value=None),
                pdf_docs_clear: gr.update(value="Docs Cleared", variant="primary", interactive=False),
                agentic_flow: gr.update(visible=True),
            }

        url_docs_upload.click(_upload_documents, [url_docs], [url_docs_upload, url_docs_clear, pdf_docs_clear, agentic_flow])
        url_docs_clear.click(_clear_documents, [], [url_docs_upload, url_docs_clear, pdf_docs_upload, pdf_docs_clear, agentic_flow])
        pdf_docs_upload.upload(_upload_documents_pdf, [pdf_docs_upload], [url_docs_clear, pdf_docs_clear, agentic_flow])
        pdf_docs_clear.click(_clear_documents, [], [url_docs_upload, url_docs_clear, pdf_docs_upload, pdf_docs_clear, agentic_flow])

        """ These helper functions set state and prompts when either the NIM or API Endpoint tabs are selected. """
        
        def _toggle_model_tab():
            return {
                group_router: gr.update(visible=False),
                group_retrieval: gr.update(visible=False),
                group_generator: gr.update(visible=False),
                group_hallucination: gr.update(visible=False),
                group_answer: gr.update(visible=False),
                router_btn: gr.update(visible=True),
                retrieval_btn: gr.update(visible=True),
                generator_btn: gr.update(visible=True),
                hallucination_btn: gr.update(visible=True),
                answer_btn: gr.update(visible=True),
            }
        
        agent_settings.select(_toggle_model_tab, [], [group_router,
                                                      group_retrieval,
                                                      group_generator,
                                                      group_hallucination,
                                                      group_answer,
                                                      router_btn,
                                                      retrieval_btn,
                                                      generator_btn,
                                                      hallucination_btn,
                                                      answer_btn])

        """ This helper function ensures only one component model settings are expanded at a time when selected. """

        def _toggle_model(btn: str):
            if btn == "Router":
                group_visible = [True, False, False, False, False]
                button_visible = [False, True, True, True, True]
            elif btn == "Retrieval Grader":
                group_visible = [False, True, False, False, False]
                button_visible = [True, False, True, True, True]
            elif btn == "Generator":
                group_visible = [False, False, True, False, False]
                button_visible = [True, True, False, True, True]
            elif btn == "Hallucination Grader":
                group_visible = [False, False, False, True, False]
                button_visible = [True, True, True, False, True]
            elif btn == "Answer Grader":
                group_visible = [False, False, False, False, True]
                button_visible = [True, True, True, True, False]
            return {
                group_router: gr.update(visible=group_visible[0]),
                group_retrieval: gr.update(visible=group_visible[1]),
                group_generator: gr.update(visible=group_visible[2]),
                group_hallucination: gr.update(visible=group_visible[3]),
                group_answer: gr.update(visible=group_visible[4]),
                router_btn: gr.update(visible=button_visible[0]),
                retrieval_btn: gr.update(visible=button_visible[1]),
                generator_btn: gr.update(visible=button_visible[2]),
                hallucination_btn: gr.update(visible=button_visible[3]),
                answer_btn: gr.update(visible=button_visible[4]),
            }

        router_btn.click(_toggle_model, [router_btn], [group_router,
                                                       group_retrieval,
                                                       group_generator,
                                                       group_hallucination,
                                                       group_answer,
                                                       router_btn,
                                                       retrieval_btn,
                                                       generator_btn,
                                                       hallucination_btn,
                                                       answer_btn])
        
        retrieval_btn.click(_toggle_model, [retrieval_btn], [group_router,
                                                                           group_retrieval,
                                                                           group_generator,
                                                                           group_hallucination,
                                                                           group_answer,
                                                                           router_btn,
                                                                           retrieval_btn,
                                                                           generator_btn,
                                                                           hallucination_btn,
                                                                           answer_btn])
        
        generator_btn.click(_toggle_model, [generator_btn], [group_router,
                                                             group_retrieval,
                                                             group_generator,
                                                             group_hallucination,
                                                             group_answer,
                                                             router_btn,
                                                             retrieval_btn,
                                                             generator_btn,
                                                             hallucination_btn,
                                                             answer_btn])
        
        hallucination_btn.click(_toggle_model, [hallucination_btn], [group_router,
                                                                                   group_retrieval,
                                                                                   group_generator,
                                                                                   group_hallucination,
                                                                                   group_answer,
                                                                                   router_btn,
                                                                                   retrieval_btn,
                                                                                   generator_btn,
                                                                                   hallucination_btn,
                                                                                   answer_btn])
        
        answer_btn.click(_toggle_model, [answer_btn], [group_router,
                                                                     group_retrieval,
                                                                     group_generator,
                                                                     group_hallucination,
                                                                     group_answer,
                                                                     router_btn,
                                                                     retrieval_btn,
                                                                     generator_btn,
                                                                     hallucination_btn,
                                                                     answer_btn])

        """ This helper function builds out the submission function call when a user submits a query. """
        
        _my_build_stream = functools.partial(_stream_predict, client, app)
        msg.submit(
            _my_build_stream, [msg, 
                               model_generator,
                               model_router,
                               model_retrieval,
                               model_hallucination,
                               model_answer,
                               prompt_generator,
                               prompt_router,
                               prompt_retrieval,
                               prompt_hallucination,
                               prompt_answer,
                               router_use_nim,
                               retrieval_use_nim,
                               generator_use_nim,
                               hallucination_use_nim,
                               answer_use_nim,
                               nim_generator_ip,
                               nim_router_ip,
                               nim_retrieval_ip,
                               nim_hallucination_ip,
                               nim_answer_ip,
                               nim_generator_port,
                               nim_router_port,
                               nim_retrieval_port,
                               nim_hallucination_port,
                               nim_answer_port,
                               nim_generator_id,
                               nim_router_id,
                               nim_retrieval_id,
                               nim_hallucination_id,
                               nim_answer_id,
                               chatbot], [msg, chatbot, actions]
        )

    page.queue()
    return page

""" This helper function verifies that a user query is nonempty. """

def valid_input(query: str):
    return False if query.isspace() or query is None or query == "" or query == '' else True

""" This helper function executes and generates a response to the user query. """

def _stream_predict(
    client: chat_client.ChatClient,
    app, 
    question: str,
    model_generator: str,
    model_router: str,
    model_retrieval: str,
    model_hallucination: str,
    model_answer: str,
    prompt_generator: str,
    prompt_router: str,
    prompt_retrieval: str,
    prompt_hallucination: str,
    prompt_answer: str,
    router_use_nim: bool,
    retrieval_use_nim: bool,
    generator_use_nim: bool,
    hallucination_use_nim: bool,
    answer_use_nim: bool,
    nim_generator_ip: str,
    nim_router_ip: str,
    nim_retrieval_ip: str,
    nim_hallucination_ip: str,
    nim_answer_ip: str,
    nim_generator_port: str,
    nim_router_port: str,
    nim_retrieval_port: str,
    nim_hallucination_port: str,
    nim_answer_port: str,
    nim_generator_id: str,
    nim_router_id: str,
    nim_retrieval_id: str,
    nim_hallucination_id: str,
    nim_answer_id: str,
    chat_history: List[Tuple[str, str]],
) -> Any:

    inputs = {"question": question, 
              "generator_model_id": model_generator, 
              "router_model_id": model_router, 
              "retrieval_model_id": model_retrieval, 
              "hallucination_model_id": model_hallucination, 
              "answer_model_id": model_answer, 
              "prompt_generator": prompt_generator, 
              "prompt_router": prompt_router, 
              "prompt_retrieval": prompt_retrieval, 
              "prompt_hallucination": prompt_hallucination, 
              "prompt_answer": prompt_answer, 
              "router_use_nim": router_use_nim, 
              "retrieval_use_nim": retrieval_use_nim, 
              "generator_use_nim": generator_use_nim, 
              "hallucination_use_nim": hallucination_use_nim, 
              "nim_generator_ip": nim_generator_ip,
              "nim_router_ip": nim_router_ip,
              "nim_retrieval_ip": nim_retrieval_ip,
              "nim_hallucination_ip": nim_hallucination_ip,
              "nim_answer_ip": nim_answer_ip,
              "nim_generator_port": nim_generator_port,
              "nim_router_port": nim_router_port,
              "nim_retrieval_port": nim_retrieval_port,
              "nim_hallucination_port": nim_hallucination_port,
              "nim_answer_port": nim_answer_port,
              "nim_generator_id": nim_generator_id,
              "nim_router_id": nim_router_id,
              "nim_retrieval_id": nim_retrieval_id,
              "nim_hallucination_id": nim_hallucination_id,
              "nim_answer_id": nim_answer_id,
              "answer_use_nim": answer_use_nim}
    
    if not valid_input(question):
        yield "", chat_history + [[str(question), "*** ERR: Unable to process query. Query cannot be empty. ***"]], gr.update(show_label=False)
    else: 
        try:
            actions = {}
            for output in app.stream(inputs):
                actions.update(output)
                yield "", chat_history + [[question, "Working on getting you the best answer..."]], gr.update(value=actions)
                for key, value in output.items():
                    final_value = value
            yield "", chat_history + [[question, final_value["generation"]]], gr.update(show_label=False)
        except Exception as e: 
            yield "", chat_history + [[question, "*** ERR: Unable to process query. Check the Monitor tab for details. ***\n\nException: " + str(e)]], gr.update(show_label=False)

_support_matrix_cache = None

def load_gpu_support_matrix() -> Dict:
    global _support_matrix_cache
    if _support_matrix_cache is None:
        matrix_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nim_gpu_support_matrix.json')
        with open(matrix_path, 'r') as f:
            _support_matrix_cache = json.load(f)
    return _support_matrix_cache
