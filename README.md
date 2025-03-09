# Overview: An Easy Button for Agentic RAG
This Retrieval Augmented Generation (RAG) application uses an agentic approach to combine web search, hallucination controls and accuracy checks with RAG. It's easy to modify because its a simple Gradio app.

> **Note**
>This app runs in [NVIDIA AI Workbench](https://docs.nvidia.com/ai-workbench/user-guide/latest/overview/introduction.html). It's a free, lightweight developer platform that you can run on your own systems to get up and running with complex AI applications and workloads in a short amount of time. 

> You may want to [**fork**](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo#forking-a-repository) this repository into your own account before proceeding. Otherwise you won't be able to fully retain any changes you make because this NVIDIA owned repository is **read-only**.

<br>

*Navigating the README:* [Application Overview](#the-agentic-rag-application) | [Get Started](#get-started) | [Deep Dive](#deep-dive) | [Self-Hosted Sizing Guide](#self-hosted-sizing-guide) | [License](#license)

<!-- Links -->
*Other Resources:* [:arrow_down: Download AI Workbench](https://www.nvidia.com/en-us/deep-learning-ai/solutions/data-science/workbench/) | [:book: User Guide](https://docs.nvidia.com/ai-workbench/) |[:open_file_folder: Other Projects](https://docs.nvidia.com/ai-workbench/user-guide/latest/quickstart/example-projects.html) | [:rotating_light: User Forum](https://forums.developer.nvidia.com/t/support-workbench-example-project-agentic-rag/303414)


## The Agentic RAG Application
#### Using the Application
1. You embed your documents (pdfs or webpages) to the vector database. 
2. You configure each of the separate components for the pipeline. For each component you can:
   * Select from a drop down of endpoints or use a self-hosted endpoint.
   * Modify the prompt.
3. You submit your query.
4. An LLM evaluates your query for relevance to the index and then routes it to the DB or to search by [Tavily](https://tavily.com/).
5. Answers are checked for hallucination and relevance. "Failing"" answers are run through the  process again.

The diagram **below** shows this agentic flow. 
 
<img src="./code/chatui/static/agentic-flow.png" width="100%" height="auto">


#### Modifying the Application

* Directly within the app you can:
   * Change the prompts for the different components, e.g. the hallucination grader.
   * Change the webpages and pdfs you want to use for the context in the RAG.
   * Select different endpoints from [build.nvidia.com](https://build.nvidia.com/explore/discover) for the inference components.
   * Configure it to use self-hosted endpoints with [NVIDIA Inference Microservices (NIMs)](https://catalog.ngc.nvidia.com/orgs/nim/teams/meta/containers/llama3-8b-instruct/tags) or [Ollama](https://hub.docker.com/r/ollama/ollama).
* You can also modify the application code to:
   * Add new endpoints and endpoint providers
   * Change the Gradio interface or the application.

> **Note** * Setting up self-hosted endpoints is relatively advanced because you will need to do it manually. 

## Get Started

The quickest path is with the pre-configured build.nvidia.com endpoints. 

#### Prerequisites for Using Pre-configured Endpoints

1. Install [AI Workbench](https://docs.nvidia.com/ai-workbench/user-guide/latest/installation/overview.html).

2. Get an NVIDIA Developer Account and an API key.
   * Go to [build.nvidia.com](https://build.nvidia.com/) and click `Login`.
   * Create account, verify email.
   * Make a Cloud Account.
   * Click your initial > `API Keys`.
   * Create and save your key.

3. Get a Tavily account and an API key.
   * Go to [Tavily](https://tavily.com/) and create an account.
   * Create an API key on the overview page.
     
4. Have some pdfs or web pages to put in the RAG.


#### Opening the Chat
   
1. Open NVIDIA AI Workbench. Select a [location to work in](https://docs.nvidia.com/ai-workbench/user-guide/latest/locations/locations.html).
   
2. Use the repository URL to clone this project with AI Workbench and wait for it to build.
   
3. Add your NVIDIA API key and the Tavily API key when prompted.

4. Open the **Chat** from Workbench. It should automatically open in a new browser tab.

5. Upload your documents and change the Router prompt to focus on your uploaded documents. 

6. Start chatting.

## Deep Dive

> **Note** This assumes you've done the **Get Started** steps.

#### Using a Self-Hosted Endpoint

Each component in the pipeline can be configured to use a self-hosted endpoint. This lets you use your own models on your own GPUs, but requires you to setup endpoints and then connect them to the RAG application.

This requires some manual steps, but if you are relatively familiar with containers and NVIDIA software, it shouldn't be too bad.

#### Prerequisites for Using a Self-Hosted Endpoint

1. You need a remote system with a sufficient GPU that you have SSH access to.

2. The remote should have the following installed:
   * Ubuntu 22.04 or higher
   * The latest NVIDIA drivers
   * The latest version of Docker
   * The latest version of the NVIDIA Container Toolkit


## Self-Hosted Sizing Guide

| GPU VRAM | Example Hardware | Compatible? |
| -------- | ------- | ------- |
| <16 GB | RTX 3080, RTX 3500 Ada | Y |
| 16 GB | RTX 4080 16GB, RTX A4000 | Y |
| 24 GB | RTX 3090/4090, RTX A5000/5500, A10/30 | Y |
| 32 GB | RTX 5000 Ada  | Y |
| 40 GB | A100-40GB | Y |
| 48 GB | RTX 6000 Ada, L40/L40S, A40 | Y |
| 80 GB | A100-80GB | Y |
| >80 GB | 8x A100-80GB | Y |




# License
This NVIDIA AI Workbench example project is under the [Apache 2.0 License](https://github.com/NVIDIA/workbench-example-agentic-rag/blob/main/LICENSE.txt)

This project may utilize additional third-party open source software projects. Review the license terms of these open source projects before use. Third party components used as part of this project are subject to their separate legal notices or terms that accompany the components. You are responsible for confirming compliance with third-party component license terms and requirements. 

| :question: Have Questions?  |
| :---------------------------|
| Please direct any issues, fixes, suggestions, and discussion on this project to the DevZone Members Only Forum thread [here](https://forums.developer.nvidia.com/t/support-workbench-example-project-agentic-rag/303414) |
