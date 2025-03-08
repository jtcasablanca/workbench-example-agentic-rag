# Overview: An Easy Button for 
This [Retrieval Augmented Generation](https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/) application uses an agentic approach to combine web search, hallucination controls and accuracy checks with RAG. Built with a Gradio front end, you can run it with AI Workbench without any complex setup.

The only requirement is curiosity. You don't need to be a developer or an expert.

*Navigating the README:* [Application Overview](#the-agentic-rag-application) | [Get Started](#get-started) | [Deep Dive](#deep-dive) | [Self-Hosted Sizing Guide](#self-hosted-sizing-guide) | [License](#license)

<!-- Links -->
*Other Resources:* [:arrow_down: Download AI Workbench](https://www.nvidia.com/en-us/deep-learning-ai/solutions/data-science/workbench/) | [:book: User Guide](https://docs.nvidia.com/ai-workbench/) |[:open_file_folder: Other Projects](https://docs.nvidia.com/ai-workbench/user-guide/latest/quickstart/example-projects.html) | [:rotating_light: User Forum](https://forums.developer.nvidia.com/t/support-workbench-example-project-agentic-rag/303414)

<br>


> **Note:**
> You may want to [**fork**](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo#forking-a-repository) this repository into your own account before proceeding. Otherwise you won't be able to fully retain any changes you make because this NVIDIA owned repository is **read-only**.

<br>

## The Agentic RAG Application
#### Using the Application
1. You embed your documents (pdfs or webpages) to the vector database. 
2. You configure the prompts for the different components, e.g. the router or retrieval grader.
3. You submit your query.
4. An LLM evaluates your query for relevance to the index and then routes it to the DB or to search by [Tavily](https://tavily.com/).
5. Answers are checked for hallucination and relevance. "Failing"" answers are run through the  process again.

The diagram **below** shows this agentic flow. 
 
<img src="./code/chatui/static/agentic-flow.png" width="100%" height="auto">


#### Modifying the Application

* You can change the prompts for the different components, e.g. the hallucination grader, directly within the front end.
* You can change the webpages and pdfs you want to use for the context in the RAG.
* You can select different endpoints for the inference components. 
  * Cloud endpoints using endpoints from [build.nvidia.com](https://build.nvidia.com/explore/discover)
  * *Advanced: Self-hosted endpoints using [NVIDIA Inference Microservices (NIMs)](https://catalog.ngc.nvidia.com/orgs/nim/teams/meta/containers/llama3-8b-instruct/tags)*
  * *Advanced: Self-hosted endpoints with Ollama.*
* You can modify the application code to add new models, add your own endpoints, change the Gradio interface, or even change the logic.

## Get Started
This app runs in [NVIDIA AI Workbench Project](https://docs.nvidia.com/ai-workbench/user-guide/latest/overview/introduction.html). 

#### Prerequisites for Using build.nvidia.com Endpoints

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

# Deep Dive
If you want to learn more about the RAG pipeline, expand the sections below.
<blockquote>
<details>
<summary>
<b> RAG Pipeline Description </b>
</summary>

Under the retrieval pipeline, the user query is first compared to documents in the vector database and the most relevant documents are retrieved. 

Another LLM call evaluates the quality of the documents. If satisfactory, it proceeds to the generation phase to produce an response augmented by this relevant context. If the agent decides the best documents are irrelevant to the query, it redirects the user query to the websearch pipeline for a better quality response (see below section). 

After generation, another set of LLMs calls evaluate the response for hallucinations and accuracy. If the generation is both faithful to the retrieved context and answers the user's query in a satisfactory manner, the response is forwarded to the user and displayed. Otherwise, the agent will either regenerate the response, or redirect the query to a web search. 

</details>

<details>
<summary>
<b> Websearch Pipeline Description</b>
</summary>

Under the web search pipeline, the user query is inputted onto the web and the search results are retrieved. Using these results, a response is generated. 

After generation, a set of LLMs calls evaluate the response for hallucinations and accuracy. If the generation is both faithful to the retrieved context and answers the user's query in a satisfactory manner, the response is forwarded to the user and displayed. Otherwise, the agent will either regenerate the response, or redirect the query to another web search. 

</details>
</blockquote>

<details>
<summary>
<b>Expand this section for a full guide of the user-configurable project settings</b>
</summary>

<img src="./code/chatui/static/example.gif" width="100%" height="auto">

When the user lands on the Chat UI application in the browser, they will see several components. On the left hand side is a standard chatbot user interface with an input box for queries (submittable with ``[ENTER]``) and a clear history button. Above this chatbot is a diagram of the agentic RAG pipeline which doubles as a progress bar indicator for any nontrivial user actions a user might take, like uploading a document. 

On the right hand side, users will see a collapsable settings panel with several tabs they may choose to navigate to and configure. 

<blockquote>
<details>
<summary>
<b>Expand for Model Settings.</b>
</summary>

<img src="./code/chatui/static/model-settings.png" width="100%" height="auto">

This tab holds every user-configurable setting for each of the LLM components of the agentic RAG pipeline: 

* Router
* Retrieval Grader
* Generator
* Hallucination Grader
* Answer Grader

Expanding any such entry will yield a panel where users can specify the model they would like to use for that particular component from a dropdown (using NVIDIA API Catalog endpoints), or they can specify their own remotely running self-hosted NVIDIA NIM custom endpoint.

Below this field is an expandable accordion where users can adjust the default prompts for that particular component's task. For example, under the Router component, users can re-write and customize their prompt to focus on only routing queries relating to LLMs and agents to the RAG pipeline and directing all other queries to the Websearch pipeline. 

</details>

<details>
<summary>
<b>Expand for Document Settings.</b>
</summary>

<img src="./code/chatui/static/doc-settings.png" width="100%" height="auto">

This tab holds every user-configurable setting for the vector database and document ingestion aspects of this agentic RAG pipeline. Users can upload their own webpages to the vector database by entering a newline-seperated list of URLs in the textbox and clicking Upload, or they can upload their own PDF files from their local machine to be stored in the vector datastore. 

</details>


<details>
<summary>
<b>Expand for Monitoring Settings.</b>
</summary>

<img src="./code/chatui/static/monitor-settings.png" width="100%" height="auto">

This tab holds the agentic RAG monitoring tools built into this application. 

* The first tool is a console that logs all the actions the agent has decided to take when processing the user query and provides a general overview into the agent's decision making.
* The second tool is an in-depth trace of the agent's actions for the last submitted query, which gives more detail into the context retrieved, websearch documents found, LLM pipeline components used, etc. when generating out the most recent response. 

</details>
</blockquote>

</details>

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
