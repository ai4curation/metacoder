# Metacoder

![Metacoder Logo](assets/metacoder-logo.png)

A unified interface for command line AI coding assistants (claude code, gemini-cli, codex, goose, qwen-coder)

```bash
# Use default coder
metacoder "Write a Python function to calculate fibonacci numbers" -w my-scripts/
...

# list coders
metacoder list-coders
Available coders:
  ✅ goose
  ✅ claude
  ✅ codex
  ✅ gemini
  ✅ qwen
  ✅ dummy

# With a specific coder
metacoder "Write a Python function to calculate fibonacci numbers" -c claude -w my-scripts/
...

# Using MCPs
metacoder "Fix issue 1234" -w path/to/my-repo --mcp-collection github_mcps.yaml
...

# Using coders for scientific QA, with a literature search MCP
metacoder "what diseases are associated with ITPR1 mutations" --mcp-collection lit_search_mcps.yaml
...
```

## Why Metacoder?

Each AI coding assistant has its own:

- Configuration format
- Command-line interface
- Working directory setup
- Means of configuring MCPs

Metacoder provides a single interface to multiple AI assistants. This makes it easier to:

- switch between agent tools in [GitHub actions pipelines](https://ai4curation.github.io/aidocs/how-tos/set-up-github-actions/)
- perform matrixed [evaluation](evaluations.md) of different agents and/or MCPs on different tasks

One of the main use cases for metacoder is evaluating *semantic coding agents*, see:

Mungall, C. (2025, July 22). Open Knowledge Bases in the Age of Generative AI (BOSC/BOKR Keynote) (abridged version). Intelligent Systems for Molecular Biology 2025 (ISMB/ECCB2025), Liverpool, UK. Zenodo. <https://doi.org/10.5281/zenodo.16461373>

Mungall, C. (2025, May 28). How to make your KG interoperable: Ontologies and Semantic Standards. NIH Workshop on Knowledge Networks, Rockville. Zenodo. <https://doi.org/10.5281/zenodo.15554695>


## Features

- Unified CLI for all supported coders
- Consistent [configuration](configuration.md) format (YAML-based)
- Unified [MCP configuration](mcps.md)
- Standardized working directory management

## MCPs

### Using the builtin MCP registry

```bash
metacoder run -r metacoder.scilit -e artl  "summarize PMID:28027860"                                                                
🤖 Using coder: goose
📁 Working directory: ./workdir
📚 Loading MCPs from registry: metacoder.scilit
   Registry MCPs: pdfreader, artl, biomcp, simple-pubmed
 ✅ MCP: artl
🚀 Running prompt: summarize PMID:28027860

==================================================
📊 RESULTS
==================================================

📝 Result:
The research paper titled "From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy: A 35-year diagnostic challenge", coded under the PubMed ID 28027860, is authored by Paolo Tinuper and Francesca Bisulli from the IRCCS Institute of Neurological Sciences, Bologna, Italy.

This paper discusses the diagnosis of nocturnal frontal lobe epilepsy (NFLE), a focal epilepsy with seizures primarily during sleep. Initially described as a motor disorder of sleep named nocturnal paroxysmal dystonia (NPD), clinicians have found it challenging to distinguish NPD from other non-epileptic nocturnal paroxysmal events like parasomnias due to unusual seizure semiology, onset during sleep, and often uninformative EEG and MRI.

In 1990, the epileptic origin of the attacks was established, leading to the introduction of the term NFLE. The diagnostic difficulties persisted, prompting a Consensus Conference in Bologna, Italy in 2014 to establish criteria. Key points of consensus elucidated the association of the seizures with sleep (not the circadian pattern), and the possible extrafrontal origin of the seizures.

The consensus meeting led to renaming the syndrome as Sleep-Related Hypermotor Epilepsy (SHE). The keywords associated with this paper include Epilepsy, Parasomnias, Nocturnal Frontal Lobe Epilepsy, Video-polysomnography, and Seizures During Sleep. The paper was published in 2017 in the journal "Seizure", and as of the last update, it was cited 34 times.

[Link to the paper](https://doi.org/10.1016/j.seizure.2016.11.023) (Subscription required)


📋 Tool uses:
  ✅ artl__get_europepmc_paper_by_id with arguments: {'identifier': '28027860'}
```

## Evaluation Framework

Metacoder includes a comprehensive evaluation framework for systematically testing and comparing AI coders, MCPs, and models.

```bash
# Run evaluation suite
metacoder eval tests/input/example_eval_config.yaml
```

Example evaluation configuration:

```yaml
name: pubmed tools evals
description: Testing coders with PubMed MCP integration

coders:
  claude: {}
  goose: {}

models:
  gpt-4o:
    provider: openai
    name: gpt-4

servers:
  pubmed:
    name: pubmed
    command: uvx
    args: [mcp-simple-pubmed]
    env:
      PUBMED_EMAIL: user@example.com

cases:
  - name: "title"
    metrics: [CorrectnessMetric]
    input: "What is the title of PMID:28027860?"
    expected_output: "From nocturnal frontal lobe epilepsy to Sleep-Related Hypermotor Epilepsy: A 35-year diagnostic challenge"
    threshold: 0.9
```

## Getting Started

- [Installation and Setup](getting-started.md)
- [Supported Coders](coders/index.md)
- [Configuration Guide](configuration.md)
- [MCP Support](mcps.md) - Extend your AI coders with additional tools
- [Evaluations](evaluations/index.md) - Test and compare AI coders