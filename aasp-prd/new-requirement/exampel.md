QueryGoal - Goal3 (NSGA-II Simulator)
'''
{
  "QueryGoal": {
    "goalId": "goal3-first-completion-001",
    "goalType": "predict_first_completion_time",
    "parameters": [
      { "key": "scenario", "value": "my_case" },
      { "key": "jobCount", "value": 40 },
      { "key": "timeLimit", "value": 600 }
    ],
    "outputSpec": [
      { "name": "predicted_completion_time", "datatype": "number" },
      { "name": "confidence", "datatype": "number" },
      { "name": "simulator_type", "datatype": "string" }
    ],
    "termination": [
      { "key": "condition", "value": "on_simulation_completed" },
      { "key": "timeout", "value": "PT10M" }
    ],
    "selectedModelRef": "aas://ModelCatalog/NSGA2SimulatorModel@1.0.0",
    "selectedModel": {
      "modelId": "NSGA2SimulatorModel",
      "MetaData": "NSGA2SimulatorMetaData.json",
      "outputs": ["predicted_completion_time","confidence","simulator_type"],
      "preconditions": { "units.time": "s", "runtime.freshness": "PT5M" },
      "container": { "image": "factory-nsga2:latest", "digest": "sha256:..." },
      "catalogVersion": "1.0.0",
      "frozenAt": @현재시간
    },
    "selectionProvenance": {
      "ruleName": "SWRL:Goal3FirstCompletion",
      "ruleVersion": "v1.0",
      "engine": "SWRL",
      "evidence": { "matched": ["goalType==predict_first_completion_time","purpose==FirstCompletionTimePrediction"] },
      "inputsHash": "sha256:...",
      "timestamp": "2025-09-22T00:00:00Z",
      "notes": ""
    }
  }
}

'''

MetaData.json
'''
{
  "modelId": "JobETAModel",
  "requiredInputs": ["JobRoute","MachineState","Calendar","SetupMatrix","WIP","Backlog"],
  "preconditions": { "units.time": "s", "runtime.freshness": "PT30S" },
  "outputs": ["completion_time","tardiness_s","sla_met"]
}

'''

bindings.yaml
'''
schema: 1
sources:
  JobRoute:
    uri: "aas://FactoryTwin/JobRoute/{jobId}"
  MachineState:
    uri: "aas://FactoryTwin/State/Machine?at={bindAt}"
    defaults: { bindAt: "@현재시간" }
  Calendar:
    uri: "file://config/factory_calendar.yaml"
  SetupMatrix:
    uri: "file://config/setup_matrix.yaml"
  WIP:
    uri: "file://state/wip/*.json"
    glob:
      sort: ["mtime:desc","name:asc"]  # 결정적 정렬
      window: { count: 5 }             # 최신 5개만
    combine:
      op: "overlay"                    # 충돌은 last-wins
      key: "partId"
  Backlog:
    uri: "file://state/backlog/*.json"
    glob:
      sort: ["mtime:desc","name:asc"]
      window: { since: "2025-09-01T00:00:00+09:00", until: "@현재시간" }
    combine:
      op: "concat"

'''