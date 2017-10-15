``` txt
    o      O        o  o              .oOOOo.
    O      o       O  O              .O     o                              o
    o      O       o  o              o
    OoOooOOo       O  O              O
    o      O .oOo. o  o  .oOo.       O   .oOOo .oOo. 'OoOo. .oOo. `oOOoOO. O  .oOo  .oOo
    O      o OooO' O  O  O   o       o.      O OooO'  o   O O   o  O  o  o o  O     `Ooo.
    o      o O     o  o  o   O        O.    oO O      O   o o   O  o  O  O O  o         O
    o      O `OoO' Oo Oo `OoO'         `OooO'  `OoO'  o   O `OoO'  O  o  o o' `OoO' `OoO'
```
---

# How to write a FASTGenomics App

Writing an app is fairly easy - there are some conventions you need to know, but otherwise you are free to use any language, tools and methods you want.
This document explains the basic structure using the example of the python "Hello Genomics" app and explains the workflow to get an app published and outlines core concepts.

## TL;DR

- Use [Docker](#docker) and any programming language
- Provide a [manifest.json](#app-structure-and-manifestjson)
- Write a [summary.md](#summary) during runtime
- Mind our [Input/Output](#file-input--output) conventions or use our [fastgenomics-py] module
- [Publish](#publishing) your application on github and deploy the image to our docker-registry

## Core concepts

There are two flavors of apps in FASTGenomics: Calculations and Visualizations.
"Calculations" perform data-intensive tasks, for example clustering whereas "visualizations" display the aforementioned results.
A visualization might take a clustering result and display a diagram for the user.

In the following section we'll give you an overview  how to write your own FASTGenomics App, that can be used in analyses, and provide information about the ingredients you need:

- Docker
- App structure and manifest
- Being part of an workflow
- File input / output
- Parameters
- Summary

### Docker

Every application runs in the FASTGenomics runtime in the form of an own docker container (which you can imagine as self-sustaining, portable workplaces).
Using docker containers helps us to eliminate the "works on my machine" problems and afford full reproducibility and transparency.
Moreover using docker containers allows you to use any programming language and framework you want to achieve your results and makes things simple for us integrating your app into the analyses if you want to.
You like Python? So do we. You are an Haskel or Julia expert? Just use it! Do you have a special configuration, which is extremely complicated or annoying to install? Just do it once and your app will work everywhere.

You never heard of Docker before? Read the article [Docker Overview](https://docs.docker.com/engine/docker-overview/).

These are the very small number of things you really need to know:

    - `Dockerfile`: This is the construction plan of your application: Here you decide what to `COPY` into, `RUN` and execute (`CMD`) within your container.
    - `docker-compose.yml` file: This file describes, how to build and start your container and providing input/output directories (volumes) for your container.
    Have a closer look at our example in order to test your application in a FASTGenomics-runtime-like environment.

In order to build and test your container proceed as follows:

    0. Install docker on your developer machine [Install Docker (CE)](https://docs.docker.com/engine/installation/)
    1. Write the Dockerfile and docker-compose.yml
    2. Build your container with
    `docker-compose -f <docker-compose.filename.yml> build`
    3. Provide sample input data (have a closer look at our example) and check paths in the `docker-compose.yml`.
    We recommend relative paths.
    4. Start the app via
    `docker-compose -f <docker-compose.filename.yml> up`

You already have a working python-script? Just clone hello-genomics and interchange the main.py, rename the directory,
and modify the paths in the Dockerfile.

One more thing: Once you started your application (container) you can list all current instances via `docker ps -a`.
To inspect the output of an application just type `docker logs <container-id>`.

### App structure and manifest.json

Your application should be structured as follows:

``` txt
.
├── docker-compose.yml (best practise)
├── Dockerfile (mandatory)
├── hello_genomics (mandatory: source code)
│   ├── __init__.py
│   ├── logging_config.py
│   └── main.py
├── manifest.json (mandatory)
├── LICENSE (mandatory)
├── README.md (mandatory)
├── requirements.txt (best practise)
├── sample_data (mandatory)
│   ├── config
│   │   └── input_file_mapping.json
│   ├── data
│   │   ├── dataset
│   │   │   ├── ...
│   │   │   └── considered_genes.tsv
│   │   └── other_app_uuid
│   │       └── output
│   ├── output
│   └── summary
├── templates (optional)
│   └── summary.md.j2
└── test (best practise)
```

FASTGenomics assumes that:

    - `manifest.json` is present in the root directory
    - `LICENSE` text is present in the root directory
    - `Dockerfile` is present in the root directory and defines a default command via `CMD` or `entry_point`
    - `sample_data` is present and available for testing (together with a `docker-compose.yml`)

Each app has to provide a `manifest.json` file with the following metadata-entries:

    - Name (of the application)
    - Type (calculation or visualization)
    - class (superior class of application)
    - Author information (name, email, organization)
    - Description (general description of the app, this can be [commonMark])
    - License (name of the license)
    - Parameters
    - Demands (A list of requirements your app might have. Currently, only GPU is supported and indicates that your app needs a GPU to do computations)
    - Input (List of files along with a key, under which files can be loaded)
    - Output (List of files along with a key, under which files can be stored)

See attached manifest.json for more information.
To validate your directory structure and manifest.json just use `check_my_app`in the [fastgenomics-py] package.

### Being part of an workflow

``` txt
    +------------+        +------------+        +------------+
    |            |        |            |        |            |
    |  app N-1   | +----> |  your app  | +----> |   app N+1  |
    |  (UUID1)   | a.txt  |  (UUID2)   | b.txt  |   (UUID3)  |
    |            |        |            |        |            |
    +------------+        +------------+        +------------+
```

Your app is part of something bigger and a piece of the puzzle:
One of our goals is to enable you to create a powerful analyses composed of small interchangeable applications like yours.
To achieve this, every app should be as universal as possible.
Also every app has to declare its in- and outputs so that we know which apps can be combined to a "workflow".

Example: If you write a classification app, we would like to know the `Type` and intent (`Usage`-field in the manifest.json) of your input and output.
As a consequence, we can avoid feeding your output into another app, which use unclustered data as input.
In future releases we would like to unify these types and intents and allow for an easy to play "Lego"-like interface for your app.

Let's assume your application gets the ID `UUID2` in the FASTGenomics runtime and runs after UUID1 and before UUID3.
Then you can have access every output of UUID1 but not UUID3 because it needs your output to run.
In the following section we describe how to access output-data from other applications or have access to the dataset.

The best method to test, if your application can be part of a workflow is by running it with sample data with the input/output of the following section.

### File input / output

We use files to talk to your app. If you write a calculation app, we expect your output as files, too.
Every app can expect to find these folders:

| Folder  | Purpose  | Mode  |
|---|---|---|
| /fastgenomics/config/   | Here you can find your parameters and configurations     | Read-only  |
| /fastgenomics/data/     | All input files will be located here                     | Read-only  |
| /fastgenomics/output/   | Output directory for your result-files                   | Read/Write |
| /fastgenomics/summary/  | Store your summary here                                  | Read/Write |

**Problem:**
To get access to data one could just simply load the data from `/fastgenomics/data/path/to/data.txt` and start your calculation but that's not how FASTGenomics works:
As your application (ID `UUID2`) is part of a larger workflow, whose applications are interchangeable, you cannot know the exact filename nor UUID at runtime.
To address this problem we introduced a file mapping mechanism, in which you define unique keys under which you would like to get the actual path of the input-file/output-file.

Using the example of the aforementioned workflow and our [fastgenomics-py] python module, a typical input/output works as follows:

Lets start with an example:
Assume you expect a normalized matrix (access-key `normalized_expression_input`) of the expression matrix as input (which is produced by app UUID1, a.txt)
and you promise to write some data quality related file "data_quality.json" (access-key `data_quality_output`).

First you have to do is to define your input/output-interface in the `manifest.json` as follows:

*manifest.json:*

``` json
"Input": {
        "normalized_expression_input": {
            "Type": "NormalizedExpressionMatrix",
            "Usage": "Genes Matrix with entrez IDs"
        },
        "other_input": {}
},
"Output": {
        "data_quality_output": {
            "Type": "DataQuality",
            "Usage": "Lists the number of genes for data quality overview.",
            "FileName": "data_quality.json"
        },
        "other_output": {}
}
```

Then you can access the files in your python code via:

*your_code.py:*

``` python
from fastgenomics import io as fg_io

normalized_input_matrix = fg_io.get_input_path('normalized_expression_input')
with normalized_input_matrix.open() as f:
    # do something like f.read()
    pass
```

Analogous to the input-file-mapping you can write output-files:

*your_code.py:*

``` python
from fastgenomics import io as fg_io

my_output_file = fg_io.get_input_path('data_quality_output')
with my_output_file.open('w') as f:
    # do something like f.write('foo')
    pass
```

**Warnings:**

    - Please do not write any files not defined in the manifest.json!
    - Do not expect internet access and even if you'd have some don't use it as reproducibility is not ensured.
    - Your will not run as root, so don't try to write to protected locations

### Parameters

Your app needs to work with a variety of datasets and workflows, so baking parameters into to app is a bad idea. Furthermore, such included parameters are not visible to anyone. So please use configuration options, which are more configurable and can be included in the summary automatically. Please use them!
You can set parameters in your `manifest.json`:

*manifest.json:*

``` json
"Parameters": {
        "delimiter": {
            "Type": "string",
            "Description": "Delimiter of the input-file",
            "Default": "\t"
        },
        "other_parameter": {}
},
```

The Type can be one of "Integer", "String", or "Float".

If you want to read them when running your app, read the file `/fastgenomics/config/parameters.json`:
Each key in the json object corresponds to the name, you defined in your manifest.json, e.g. `delimiter`.
In contrast to the `manifest.json` describing the app, the `parameters.json` defines the parameter values that are used in the current instance of the app.
For different datasets and workflows these values could be changed by the users later. Initially, the values should be set to the default as described in manifest.json.

We highly recommend the usage of the [fastgenomics-py] module as follows:

*your_code.py:*

``` python
from fastgenomics import io as fg_io
...
parameters = fg_io.get_parameters()
...
delimiter = fg_io.get_parameter('delimiter')
...
```

**Hints:**

- Currently we did not implement runtime-parameters yet so the default values are used by our python module.
- If you use a random seed (e.g. in the k-means algorithm) fix the seed and add the seed to the parameters, otherwise your results will not be reproducible.
- Denote default values of parameters in your `manifest.json`

### Summary

Reproducibility is a core goal of FASTGenomics, but it is difficult to achieve this without your help.
Docker helps to freeze the exact code your app is using, but code without documentation is difficult to use,
so an app is expected to have a documentation and provide a so called "summary" of its results (as [CommonMark]).
You need to store it as `/fastgenomics/summary/summary.md` - otherwise it would be ignored.

While a generic documentation of your application is specified in the manifest.json,
we encourage you to describe the scientific meaning of the results achieved my your application in the summary 
in terms of a "abstract, methods and results"-section of a publication.
To do so, your application needs to describe all operations applied to the data and all achieved results,
which only can be described during and after runtime of your application as it doesn't know the input data yet.

For example: "... and identified 14 clusters ..."

*your_code.py:*

``` python
from fastgenomics import io as fg_io

summary = "<content>"

summary_file = fg_io.get_summary_path()
with summary_file.open('w') as f_sum:
    f_sum.write(summary)
```

The summary is a [CommonMark] file your app has to write every time it runs.
The file should follow these rules:

- Use only Headings h3-h5 (###, ####, #####)
- Mandatory sections:
  - Abstract (without heading, just the first lines in the document)
  - Results (h3 heading, upper case, optional for visualizations)
  - Details (h3 heading, upper case, optional for visualizations)
  - Parameters (h3 heading, upper case)
- Do not provide information like author and lists of input/output files - these information are filled in automatically.
- Only use global parameters denoted in your `manifest.json`, don't use constants besides parameters
- Denote default values of parameters in your `manifest.json`
- Report on all parameters/settings (even default settings)
- Report or fix random seed
- Report on own offline databases (source, date)
- Describe every step of your calculation in the 'Details'-section
- Only write files as denoted in your `manifest.json`

### Miscellaneous

#### Logging

You might wonder how your app can output progress- debug information etc.
There is an easy solution for this: simply write output the stdout /stderr.
For example print("hello world"), the user of your app can then see this output.

For enhanced debugging and logging we recommend logging-modules like the python `logging` module (see hello genomics).

To gain access to the output of your running/terminated application type:
`docker ps -a` to list all (`-a`) running and terminated apps and identify the container-id of your application.
Then type `docker logs <container-id>` to access logs.

#### Versions

Most of the time, you want to use version numbers to differentiate versions of your application.
This version number is not included in your manifest.json, since we use a Docker feature: tags.
Every Docker image has a tag, which can be used as the version number.
You can see this with many images, where the part after ":" is the tag.
E.g.: `python:3.6.1` denotes that we use the python image, with Python version 3.6.1.

You can use any tag except `:latest`, but we recommend an incrementing integer or a Major.Minor.Patch scheme.
Please make sure that each push to our registry uses a new tag, do not attempt to overwrite older versions!

**We highly encourage you to pin all of your dependencies/requirements to ensure reproducibility.**

See also  [Publishing](##Publishing) for more details.

#### Exit-Code

Please make sure that your app terminates either with Exit code 0 (success) or a nonzero Exit code if you encountered an error.
This should be normal behavior for a command line application anyway, but please check it.

#### User

We use a non Root User when running the app. So do not try to use a specific user in your app-
Best practice: Develop you app with a non-root user, e. g. the guest account. See the docker [docker-user] instruction.

## Publishing

Checklist:

1. Write your code, respect the file locations as specified in this readme.
2. Write a Dockerfile for your App.
3. Write a manifest.json, which defines the interfaces of your app and provides some additional information. Use english for every description!
4. Write a docker-compose.yml and provide sample_date
5. Ship and respect licences
6. Write the input_file_mapping.json
7. Build and test your application by
   `docker-compose -f <your_compose_file> build`
    and `docker-compose -f <your_compose_file> up`
8. Check your image size: `docker images` gives you an overview.
   Please go easy with image sizes as starting procedure and memory is limited.
   Think twice before submitting images larger than 1GB.
9. Push your image to our registry:
    1. Login to our registry:
       `docker login apps.fastgenomics.org -u fastgenomicsPublic -p /JCiDiuZ6AW/0=ufmvogVzc4/RQfcY0U`
    2. We expect this naming convention for your registry and tag:
        apps.fastgenomics.org/#your name#/#name of your app#:#version#

        For example: apps.fastgenomics.org/teamfastgenomics/ourfirstapp:0.0.1

    3. Build your app using `docker build -t <registry/image_name:tag>`
    4. Push to our registry: `docker push <registry/image_name:tag>`
    5. For details about tagging, see [docker tag](https://docs.docker.com/engine/reference/commandline/tag/#examples).
10. Smile: You did it! You just wrote and published your first FASTGenomics application!

## Advanced topics

### Input/Output

Using the example of the aforementioned workflow, a typical directory tree your app `UUID2` could see under `/fastgenomics/` looks like the following tree:

``` txt
(/fastgenomics/)
    .
    ├── config
    │   └── input_file_mapping.json
    ├── data
    │   ├── UUID1
    │   │   └── output
    │   │       └── a.txt
    │   ├── UUID2
    │   │   └── output
    │   │       └── b.txt
    │   └── dataset
    │       ├── cells.tsv
    │       ├── data_quality.json
    │       ├── expressions_entrez.tsv
    │       ├── genes_considered_all.tsv
    │       ├── genes_considered_expressed.tsv
    │       ├── genes_considered_unexpressed.tsv
    │       ├── genes_entrez.tsv
    │       ├── genes_nonentrez.tsv
    │       ├── genes.tsv
    │       ├── genes_unconsidered_all.tsv
    │       ├── genes_unconsidered_expressed.tsv
    │       ├── genes_unconsidered_unexpressed.tsv
    │       ├── manifest.json
    │       └── unconsidered_genes.tsv
    ├── output
    │   └── b.txt
    └── summary
        └── summary.md
```

``` json

"Input": {
        "normalized_expression_input": {
            "Type": "NormalizedExpressionMatrix",
            "Usage": "Genes Matrix with entrez IDs"
        },
        "other_input": {}
},
"Output": {
        "data_quality_output": {
            "Type": "DataQuality",
            "Usage": "Lists the number of genes for data quality overview.",
            "FileName": "data_quality.json"
        },
        "other_output": {}
}
```

The directory "UUID3" is missing because of the order of applications: your application has to run before UUID3, hence it isn't visible yet.

The actual filename can be looked up in `/fastgenomics/config/input_file_mapping.json`, which looks like the following example:

``` json
{
    "normalized_expression": "UUID1/a.txt"
}
```

This file will be created by the FASTGenomics runtime.

**Hint:**
If you would like to test your application in a FASTGenomics runtime-like environment, you have to provide these directories and the input_file_mapping.json on your own.
As mechanisms could change we highly recommend the usage of our [fastgenomics-py] python module as described above.

[commonMark]: http://spec.commonmark.org/0.27
[fastgenomics-py]: http://www.github.com/fastgenomics/fastgenomics-py
[docker-user]: https://docs.docker.com/engine/reference/builder/#user
