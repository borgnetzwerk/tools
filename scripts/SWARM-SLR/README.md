# SWARM-SLR
**S**treamlined **W**orkflow **A**utomation **R**equirements for **M**achine-readable **S**ystematic **L**iterature **R**eviews

## Stage I
[SWARM-SLR_Stage_I.ipynb](SWARM-SLR_Stage_I.ipynb)

## Stage II
[SWARM-SLR_Stage_II.ipynb](SWARM-SLR_Stage_II.ipynb)

## Stage III
[SWARM-SLR_Stage_III.ipynb](SWARM-SLR_Stage_III.ipynb)

## Stage IV
[SWARM-SLR_Stage_IV.ipynb](SWARM-SLR_Stage_IV.ipynb)

## Background
SWARM-SLR currently postulates 65 requirements for a machine-readable SLR. These have been [evaluated](data/evaluation.ipynb), alongside with the question, which tools already address which of these requirements.

If you too want to contribute your knowledge, click here:
* [Requirements Review](https://survey.uni-hannover.de/index.php/555283?lang=en)
* [Tool Assessment](https://survey.uni-hannover.de/index.php/628237?lang=en)
  * If you want to evaluate the "SWARM-SLR Workflow" which is descibed in this repository, just select "other" on the first question of the [Tool Assessment](https://survey.uni-hannover.de/index.php/628237?lang=en), and enter ```SWARM-SLR``` as the tool name.
  * You can use this field to assess any other tool that might help the SWARM-SLR as well.

### Requirements
![A boxplot showing the survey replies to the survey "Tool Assisted Literature Surveys - A Requirements Review". It depicts a general agreement upon the validity of most of these requirements, with selected dips into disagreement.](<data/visualization/Tool Assisted Literature Surveys - A Requirements Review.png>)

### Tools
In a survey with 22 replies, 11 tools have been evaluated, 6 of them by multiple replies.
![A boxplot showing the survey replies to the survey "Tool Assisted Literature Surveys - A Tool Review". It depicts many different tools covering almost all of the requirements, with some requirements not being fully covered.](<data/visualization/Tool Assisted Literature Surveys - A Tool Review.png>)

One of these tools is the "SWARM-SLR Workflow", the guided toolchain in this repository.
![A boxplot showing the survey replies to the survey "Tool Assisted Literature Surveys - A Tool Review", specifically only for the "SWARM-SLR Workflow" presented here in the repository. It depicts a relatively consistend support for most of the SLR stages, with medium support early on, major support in the middle stages, medium support in the later stages. Some requirements are also not adressed at all.](<data/visualization/SWARM-SLR Workflow.png>)

## Citing SWARM-SLR
This work has been submitted to TPDL [[1]](https://arxiv.org/abs/2407.18657), accepted, presented [[2]](https://github.com/borgnetzwerk/tools/blob/main/scripts/SWARM-SLR/SWARM-SLR.pdf), and published [[3]](https://doi.org/10.1007/978-3-031-72437-4_2). If you want to cite SWARM-SLR:

```
@InProceedings{wittenborg_swarm-slr_2024,
  author="Wittenborg, Tim and Karras, Oliver and Auer, S{\"o}ren",
  title="SWARM-SLR - Streamlined Workflow Automation for Machine-Actionable Systematic Literature Reviews",
  booktitle="Linking Theory and Practice of Digital Libraries",
  year="2024",
  keywords = {Systematic Literature Review, Workflow Automation, Requirement, Software Tool, Crowdsourcing},
  publisher="Springer Nature Switzerland",
  pages="20--40",
  isbn="978-3-031-72437-4"
}
```
